import json,csv,collections,math,re,hashlib,time,sys
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer

BASE=Path("/vercel")
TOP=100
TOKEN=re.compile(r"\w+",re.UNICODE)
def tokenize(t):return [w for w in TOKEN.findall(t.lower()) if len(w)>1]
def load(ds):
 p=BASE/"datasets"/ds
 corpus=[json.loads(x) for x in (p/"corpus.jsonl").read_text().splitlines()]
 queries={x["_id"]:x["text"] for x in (json.loads(s) for s in (p/"queries.jsonl").read_text().splitlines())}
 qrels=collections.defaultdict(dict)
 with (p/"qrels/test.tsv").open() as f:
  for row in csv.reader(f,delimiter="\t"):
   if not row or row[0].lower() in ["query-id","query_id"]:continue
   q,d,label=row[:3]
   if int(label)>0:qrels[q][d]=int(label)
 ids=[c["_id"] for c in corpus]; txt=[(c.get("title","")+"\n"+c.get("text","")).strip() for c in corpus]
 qids=sorted(qrels); return ids,txt,qids,[queries[q] for q in qids],qrels
class BM25:
 def __init__(self,txt):
  self.N=len(txt);self.index=collections.defaultdict(list);df=collections.Counter();lens=[]
  for i,x in enumerate(txt):
   counter=collections.Counter(tokenize(x));lens.append(sum(counter.values()))
   for t,n in counter.items():self.index[t].append((i,n));df[t]+=1
  self.lens=np.asarray(lens,dtype=float);self.av=self.lens.mean()
  self.idf={t:math.log(1+(self.N-n+0.5)/(n+0.5)) for t,n in df.items()}
 def score(self,q):
  z=np.zeros(self.N); norm=1.2*(1-.75+.75*self.lens/self.av)
  for t in set(tokenize(q)):
   for i,tf in self.index.get(t,[]):z[i]+=self.idf[t]*tf*2.2/(tf+norm[i])
  return z
def top(scores,ids,exclude_zero):
 ii=[i for i,s in enumerate(scores) if np.isfinite(s) and (not exclude_zero or s>0)]
 ii.sort(key=lambda i:(-float(scores[i]),ids[i]))
 return [ids[i] for i in ii[:TOP]]
def rrf(a,b):
 result=[]
 for aa,bb in zip(a,b):
  s=collections.defaultdict(float)
  for run in [aa,bb]:
   for k,doc in enumerate(run,1):s[doc]+=1/(60+k)
  result.append([d for d,_ in sorted(s.items(),key=lambda x:(-x[1],x[0]))[:TOP]])
 return result
def evalone(ids,txt,qids,qs,rels,ds,model):
 t0=time.time()
 bm=BM25(txt);rb=[top(bm.score(q),ids,True) for q in qs]
 vt=TfidfVectorizer(analyzer="word",ngram_range=(1,2),lowercase=True,sublinear_tf=True,norm="l2",dtype=np.float32)
 a=vt.fit_transform(txt);qmat=vt.transform(qs)
 rw=[top(np.asarray((qmat[i]@a.T).toarray()).ravel(),ids,True) for i in range(len(qs))]
 vc=TfidfVectorizer(analyzer="char_wb",ngram_range=(3,5),lowercase=True,sublinear_tf=True,norm="l2",dtype=np.float32)
 ac=vc.fit_transform(txt);qc=vc.transform(qs)
 rc=[top(np.asarray((qc[i]@ac.T).toarray()).ravel(),ids,True) for i in range(len(qs))]
 print("LEXICAL_FINISHED",ds,round(time.time()-t0,1),flush=True)
 em=model.encode(txt,batch_size=32,show_progress_bar=False,normalize_embeddings=True,convert_to_numpy=True)
 eq=model.encode(qs,batch_size=32,show_progress_bar=False,normalize_embeddings=True,convert_to_numpy=True)
 scores=eq@em.T
 rd=[top(row,ids,False) for row in scores]
 hy=rrf(rb,rd)
 methods={"BM25":rb,"TF-IDF palabras":rw,"TF-IDF caracteres":rc,"MiniLM":rd,"BM25 + MiniLM (RRF)":hy}
 out=BASE/"resultados"/ds;out.mkdir(parents=True,exist_ok=True)
 results={};deltas=[];rows=[]
 for method,runs in methods.items():
  per=[]
  for j,(qid,query,rank) in enumerate(zip(qids,qs,runs)):
   truth=rels[qid];gain=[truth.get(r,0) for r in rank[:10]]
   dcg=sum((2**v-1)/math.log2(i+2) for i,v in enumerate(gain))
   ideal=sum((2**v-1)/math.log2(i+2) for i,v in enumerate(sorted(truth.values(),reverse=True)[:10]))
   hits=[bool(x) for x in gain]
   metric={"nDCG@10":dcg/ideal if ideal else 0,"Recall@10":sum(hits)/len(truth) if truth else 0,"MRR@10":next((1/(i+1) for i,x in enumerate(hits) if x),0),"Hit@10":float(any(hits))}
   per.append(metric)
   rows.append({"method":method,"qid":qid,"query":query,"top10":";".join(rank[:10]),"relevantes":";".join(truth.keys()),**metric})
  results[method]={"per":per,**{k:float(np.mean([m[k] for m in per])) for k in ["nDCG@10","Recall@10","MRR@10","Hit@10"]}}
 for method in methods:
  if method=="BM25":continue
  diff=np.array([x["nDCG@10"]-y["nDCG@10"] for x,y in zip(results[method]["per"],results["BM25"]["per"])])
  random=np.random.default_rng(20261013)
  samples=diff[random.integers(0,len(diff),size=(2000,len(diff)))].mean(axis=1)
  deltas.append({"method":method,"delta":round(float(diff.mean()),4),"CI95":[round(float(v),4) for v in np.quantile(samples,[.025,.975])],"wins":int((diff>1e-9).sum()),"losses":int((diff< -1e-9).sum()),"ties":int((abs(diff)<=1e-9).sum())})
 with (out/"per_query.csv").open("w",newline="",encoding="utf-8") as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 result={"dataset":ds,"docs":len(ids),"queries":len(qids),"methods":{k:{kk:round(vv,4) for kk,vv in v.items() if kk!="per"} for k,v in results.items()},"compared_to_BM25":deltas,"elapsed_s":round(time.time()-t0,1)}
 (out/"summary.json").write_text(json.dumps(result,indent=2,ensure_ascii=False))
 print("RESULT_JSON",json.dumps(result,ensure_ascii=False),flush=True)
 return result
def main():
 t=time.time()
 print("MODEL_START",flush=True)
 model=SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2",device="cpu")
 print("MODEL_READY",round(time.time()-t,1),flush=True)
 for ds in ["scifact","nfcorpus"]:
  ids,txt,qids,qs,qrels=load(ds)
  evalone(ids,txt,qids,qs,qrels,ds,model)
 print("COMPLETE",flush=True)
if __name__=="__main__":main()

