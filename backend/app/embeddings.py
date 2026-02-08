import hashlib

import numpy as np


def compute_embedding(image_bytes: bytes, dims: int = 256) -> list[float]:
    digest = hashlib.sha256(image_bytes).digest()
    repeated = (digest * (dims // len(digest) + 1))[:dims]
    vector = np.frombuffer(repeated, dtype=np.uint8).astype(np.float32)
    vector = (vector - vector.mean()) / (vector.std() + 1e-6)
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector.tolist()
    return (vector / norm).tolist()


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    array_a = np.array(vec_a, dtype=np.float32)
    array_b = np.array(vec_b, dtype=np.float32)
    denom = (np.linalg.norm(array_a) * np.linalg.norm(array_b)) + 1e-6
    return float(np.dot(array_a, array_b) / denom)
