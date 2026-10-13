"""Download the official BEIR test corpora, verify MD5, and extract safely."""
from pathlib import Path
from urllib.request import urlretrieve
from hashlib import md5
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE / "datasets"
FILES = {
    "scifact": "5f7d1de60b170fc8027bb7898e2efca1",
    "nfcorpus": "a89dba18a62ef92f7d323ec890a0d38d",
}

def checksum(path):
    digest = md5()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    for name, expected in FILES.items():
        archive = ROOT / f"{name}.zip"
        if not archive.exists():
            url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{name}.zip"
            print("Downloading", url, flush=True)
            urlretrieve(url, archive)
        if checksum(archive) != expected:
            raise ValueError(f"MD5 mismatch for {archive}. Delete the file before retrying.")
        with ZipFile(archive) as bundle:
            for file in bundle.infolist():
                target = (ROOT / file.filename).resolve()
                if not target.is_relative_to(ROOT.resolve()):
                    raise ValueError("Unsafe archive entry")
            bundle.extractall(ROOT)
        print(name, "verified", flush=True)

if __name__ == "__main__":
    main()
