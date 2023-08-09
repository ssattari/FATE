from typing import List, Optional, Tuple

import numpy as np
import torch
from heu import numpy as hnp
from heu import phe

V = torch.Tensor
EV = "FixedpointPaillierVector"
FV = "FixedpointVector"


class SK:
    def __init__(self, sk: hnp.HeKit) -> None:
        self.sk = sk.decryptor()

    def decrypt_to_encoded(self, vec: EV) -> FV:
        return self.sk.decrypt(vec)


class PK:
    def __init__(self, kit: hnp.HeKit):
        self.kit = kit
        self.encryptor = kit.encryptor()

    def encrypt_encoded(self, vec: FV, obfuscate: bool) -> EV:
        return self.encryptor.encrypt(vec)

    def encrypt_encoded_scalar(self, val, obfuscate) -> EV:
        return self.encryptor.encrypt(val)


class Coder:
    def __init__(self, kit: hnp.HeKit):
        self.kit = kit
        self.float_encoder = kit.float_encoder()
        self.int_encoder = kit.integer_encoder()

    def encode_tensor(self, tensor: V, dtype: torch.dtype = None) -> FV:
        if dtype is None:
            dtype = tensor.dtype
        if dtype == torch.float64:
            return self.kit.array(tensor.detach().numpy(), self.float_encoder)
        if dtype == torch.float32:
            return self.kit.array(tensor.detach().numpy(), self.float_encoder)
        if dtype == torch.int64:
            return self.kit.array(tensor.detach().numpy(), self.int_encoder)
        if dtype == torch.int32:
            return self.kit.array(tensor.detach().numpy(), self.int_encoder)
        raise NotImplementedError(f"{dtype} not supported")

    def decode_tensor(self, tensor: FV, dtype: torch.dtype, shape: torch.Size = None) -> V:
        if dtype == torch.float64:
            data = torch.tensor(tensor.to_numpy(self.float_encoder)).type(dtype)
        elif dtype == torch.float32:
            data = torch.tensor(tensor.to_numpy(self.float_encoder)).type(dtype)
        elif dtype == torch.int64:
            data = torch.tensor(tensor.to_numpy(self.int_encoder)).type(dtype)
        elif dtype == torch.int32:
            data = torch.tensor(tensor.to_numpy(self.int_encoder)).type(dtype)
        else:
            raise NotImplementedError(f"{dtype} not supported")
        if shape is not None:
            data = data.reshape(shape)
        return data

    def encode_vec(self, vec: V, dtype: torch.dtype = None) -> FV:
        if dtype is None:
            dtype = vec.dtype
        if dtype == torch.float64:
            return self.encode_f64_vec(vec)
        if dtype == torch.float32:
            return self.encode_f32_vec(vec)
        if dtype == torch.int64:
            return self.encode_i64_vec(vec)
        if dtype == torch.int32:
            return self.encode_i32_vec(vec)
        raise NotImplementedError(f"{vec.dtype} not supported")

    def decode_vec(self, vec: FV, dtype: torch.dtype) -> V:
        if dtype == torch.float64:
            return self.decode_f64_vec(vec)
        if dtype == torch.float32:
            return self.decode_f32_vec(vec)
        if dtype == torch.int64:
            return self.decode_i64_vec(vec)
        if dtype == torch.int32:
            return self.decode_i32_vec(vec)
        raise NotImplementedError(f"{dtype} not supported")

    def encode(self, val, dtype=None) -> FV:
        if isinstance(val, torch.Tensor):
            assert val.ndim == 0, "only scalar supported"
            if dtype is None:
                dtype = val.dtype
            val = val.item()
        if dtype == torch.float64:
            return self.encode_f64(val)
        if dtype == torch.float32:
            return self.encode_f32(val)
        if dtype == torch.int64:
            return self.encode_i64(val)
        if dtype == torch.int32:
            return self.encode_i32(val)
        raise NotImplementedError(f"{dtype} not supported")

    def encode_f64(self, val: float):
        return self.kit.array(val, self.float_encoder)

    def decode_f64(self, val):
        return torch.tensor(val.to_numpy(self.float_encoder)).type(torch.float64)

    def encode_i64(self, val: int):
        return self.kit.array(val, self.float_encoder)

    def decode_i64(self, val):
        return torch.tensor(val.to_numpy(self.float_encoder)).type(torch.int64)

    def encode_f32(self, val: float):
        return self.kit.array(val, self.float_encoder)

    def decode_f32(self, val):
        return torch.tensor(val.to_numpy(self.float_encoder)).type(torch.float32)

    def encode_i32(self, val: int):
        return self.kit.array(val, self.int_encoder)

    def decode_i32(self, val):
        return torch.tensor(val.to_numpy(self.int_encoder)).type(torch.int32)

    def encode_f64_vec(self, vec: torch.Tensor):
        return self.kit.array(vec.detach().numpy(), self.float_encoder)

    def decode_f64_vec(self, vec):
        return torch.tensor(vec.to_numpy(self.float_encoder)).type(torch.float64)

    def encode_i64_vec(self, vec: torch.Tensor):
        return self.kit.array(vec.detach().numpy(), self.int_encoder)

    def decode_i64_vec(self, vec):
        return torch.tensor(vec.to_numpy(self.int_encoder)).type(torch.int64)

    def encode_f32_vec(self, vec: torch.Tensor):
        return self.kit.array(vec.detach().numpy(), self.float_encoder)

    def decode_f32_vec(self, vec):
        return torch.tensor(vec.to_numpy(self.float_encoder)).type(torch.float32)

    def encode_i32_vec(self, vec: torch.Tensor):
        return self.kit.array(vec.detach().numpy(), self.int_encoder)

    def decode_i32_vec(self, vec):
        return torch.tensor(vec.to_numpy(self.int_encoder)).type(torch.int32)


def keygen(key_size):
    phe_kit = phe.setup(phe.SchemaType.ZPaillier, key_size)
    kit = hnp.HeKit(phe_kit)
    pub_kit = hnp.setup(kit.public_key())
    return SK(kit), PK(pub_kit), Coder(pub_kit)


class evaluator:
    @staticmethod
    def add(a: EV, b: EV, pk: PK):
        return pk.kit.evaluator().add(a, b)

    @staticmethod
    def add_plain(a: EV, b: V, pk: PK, coder: Coder, output_dtype=None):
        if output_dtype is None:
            output_dtype = b.dtype
        encoded = coder.encode_vec(b, dtype=output_dtype)
        encrypted = pk.encrypt_encoded(encoded, obfuscate=False)
        return pk.kit.evaluator().add(a, encrypted)

    @staticmethod
    def add_plain_scalar(a: EV, b, pk: PK, coder: Coder, output_dtype):
        encoded = coder.encode(b, dtype=output_dtype)
        encrypted = pk.encrypt_encoded_scalar(encoded, obfuscate=False)
        return pk.kit.evaluator().add(a, encrypted)

    @staticmethod
    def sub(a: EV, b: EV, pk: PK):
        return pk.kit.evaluator().sub(a, b)

    @staticmethod
    def sub_plain(a: EV, b: V, pk: PK, coder: Coder, output_dtype=None):
        if output_dtype is None:
            output_dtype = b.dtype
        encoded = coder.encode_vec(b, dtype=output_dtype)
        encrypted = pk.encrypt_encoded(encoded, obfuscate=False)
        return pk.kit.evaluator().sub(a, encrypted)

    @staticmethod
    def sub_plain_scalar(a: EV, b, pk: PK, coder: Coder, output_dtype):
        encoded = coder.encode(b, dtype=output_dtype)
        encrypted = pk.encrypt_encoded_scalar(encoded, obfuscate=False)
        return pk.kit.evaluator().sub(a, encrypted)

    @staticmethod
    def rsub(a: EV, b: EV, pk: PK):
        return evaluator.sub(b, a, pk)

    @staticmethod
    def rsub_plain(a: EV, b: V, pk: PK, coder: Coder, output_dtype=None):
        if output_dtype is None:
            output_dtype = b.dtype
        encoded = coder.encode_vec(b, dtype=output_dtype)
        encrypted = pk.encrypt_encoded(encoded, obfuscate=False)
        return evaluator.rsub(a, encrypted, pk)

    @staticmethod
    def rsub_plain_scalar(a: EV, b, pk: PK, coder: Coder, output_dtype):
        encoded = coder.encode(b, dtype=output_dtype)
        encrypted = pk.encrypt_encoded_scalar(encoded, obfuscate=False)
        return evaluator.rsub(a, encrypted, pk)

    @staticmethod
    def mul_plain(a: EV, b: V, pk: PK, coder: Coder, output_dtype=None):
        if output_dtype is None:
            output_dtype = b.dtype
        encoded = coder.encode_vec(b, dtype=output_dtype)
        return pk.kit.evaluator().mul(a, encoded)

    @staticmethod
    def mul_plain_scalar(a: EV, b, pk: PK, coder: Coder, output_dtype):
        encoded = coder.encode(b, dtype=output_dtype)
        return pk.kit.evaluator().mul(a, encoded)

    @staticmethod
    def matmul(a: EV, b: V, a_shape, b_shape, pk: PK, coder: Coder, output_dtype):
        encoded = coder.encode_vec(b.reshape(b_shape), dtype=output_dtype)
        # TODO: move this to python side so other protocols can use it without matmul support?
        return pk.kit.evaluator().matmul(a, encoded)

    @staticmethod
    def rmatmul(a: EV, b: V, a_shape, b_shape, pk: PK, coder: Coder, output_dtype):
        encoded = coder.encode_vec(b, dtype=output_dtype)
        return pk.kit.evaluator().matmul(encoded, a)

    @staticmethod
    def zeros(pk: PK, size) -> EV:
        return pk.encryptor.encrypt(pk.kit.array(np.zeros(size, np.int), pk.kit.integer_encoder()))

    @staticmethod
    def i_add(pk: PK, a: EV, b: EV, sa=0, sb=0, size: Optional[int] = None) -> None:
        """
        inplace add, a[sa:sa+size] += b[sb:sb+size], if size is None, then size = min(a.size - sa, b.size - sb)
        Args:
            pk: the public key
            a: the vector to add to
            b: the vector to add
            sa: the start index of a
            sb: the start index of b
            size: the size to add
        """
        if a is b:
            a.iadd_vec_self(sa, sb, size, pk.pk)
        else:
            a.iadd_vec(b, sa, sb, size, pk.pk)

    @staticmethod
    def slice(a: EV, start: int, size: int) -> EV:
        """
        slice a[start:start+size]
        Args:
            a: the vector to slice
            start: the start index
            size: the size to slice

        Returns:
            the sliced vector
        """
        return a.slice(start, size)

    @staticmethod
    def intervals_sum_with_step(pk: PK, a: EV, intervals: List[Tuple[int, int]], step: int):
        """
        sum in the given intervals, with step size

        for example:
            if step=2, intervals=[(0, 4), (6, 12)], a = [a0, a1, a2, a3, a4, a5, a6, a7,...]
            then the result is [a0+a2, a1+a3, a6+a8+a10, a7+a9+a11]
        """
        return a.intervals_sum_with_step(pk.pk, intervals, step)

    @staticmethod
    def chunking_cumsum_with_step(pk: PK, a: EV, chunk_sizes: List[int], step: int):
        """
        chunking cumsum with step size

        for example:
            if step=2, chunk_sizes=[4, 2, 6], a = [a0, a1, a2, a3, a4, a5, a6, a7,...a11]
            then the result is [a0, a1, a0+a2, a1+a3, a4, a5, a6, a7, a6+a8, a7+a9, a6+a8+a10, a7+a9+a11]
        Args:
            pk: the public key
            a: the vector to cumsum
            chunk_sizes: the chunk sizes, must sum to a.size
            step: the step size, cumsum with skip step-1 elements
        Returns:
            the cumsum result
        """
        return a.chunking_cumsum_with_step(pk.pk, chunk_sizes, step)
