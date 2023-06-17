import time
import zlib
import os
import loguru
import asyncio
from typing import AsyncGenerator, Tuple, Union


async def find_files(root: str) -> AsyncGenerator[str, None]:
    """返回目录下所有文件的路径"""
    for root, _, files in os.walk(root):
        for filename in files:
            yield os.path.join(root, filename)


async def decrypt_file(file_path: str) -> Union[None, Tuple[str, bytes]]:
    """解密文件"""
    with open(file_path, 'rb') as fp:
        encrypt_data = fp.read()

    # 检查文件头
    if not encrypt_data.startswith(b"\xff\xd9\xff\xd7"):
        return None

    # 解密和解压缩
    xor_key = b"\xd6\x02\x08\x00\xf4\xfe\xff\x3f\x01\x00\x00\x00\xd0\xca\x01\x00"
    key = xor_key * (len(encrypt_data) // 0xF + 1)
    key = key[:len(encrypt_data)]
    decrypt_data = bytes(a ^ b for a, b in zip(encrypt_data[8:], key))
    out_data = zlib.decompress(decrypt_data)

    return file_path, out_data


async def process_files(file_paths: AsyncGenerator[str, None]) -> None:
    async for file_path in file_paths:
        result = await decrypt_file(file_path)
        if result is None:
            loguru.logger.error(f"Decrypt failed for a file :(")
        else:
            file_path, out_data = result
            dirs = os.path.join("decrypted", os.path.dirname(file_path))
            os.makedirs(dirs, exist_ok=True)

            output_file_path = os.path.join("decrypted", file_path)
            with open(output_file_path, 'wb') as fp:
                fp.write(out_data)

            loguru.logger.success(f"{file_path} decrypt successfully!")


async def main() -> None:
    if not os.path.exists("decrypted"):
        os.mkdir("decrypted")

    begin_time = time.time()

    async for file_path in find_files("file"):
        result = await decrypt_file(file_path)
        if result is None:
            loguru.logger.error(f"{file_path} decrypt failed :(")
        else:
            file_path, out_data = result
            dirs = os.path.join("decrypted", os.path.dirname(file_path))
            os.makedirs(dirs, exist_ok=True)

            output_file_path = os.path.join("decrypted", file_path)
            with open(output_file_path, 'wb') as fp:
                fp.write(out_data)

            loguru.logger.success(f"{file_path} decrypt successfully!")

    end_time = time.time()
    loguru.logger.info(f"解密完成，耗时{end_time - begin_time}s")


if __name__ == '__main__':
    asyncio.run(main())
