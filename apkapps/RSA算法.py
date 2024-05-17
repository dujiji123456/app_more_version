import rsa
import os
import base64


class RSA():
    def __init__(self):
        self.current_directory = os.path.dirname(__file__)
        # 加载 PEM 格式的公钥
        self.public_path = os.path.join(self.current_directory, "public_key.pem")
        with open(self.public_path, 'rb') as file:
            self.public_key = rsa.PublicKey.load_pkcs1(file.read())

        # 读取私钥文件
        self.private_path = os.path.join(self.current_directory, "private_key.pem")
        with open(self.private_path, 'rb') as file:
            self.private_key = rsa.PrivateKey.load_pkcs1(file.read())

    # def encrypt(self, message):#删掉
    #     # 使用RSA公钥加密数据
    #     encrypted_data = base64.b64encode(rsa.encrypt(message.encode(), self.public_key)).decode()
    #     return encrypted_data

    def decrypt(self, encrypted_data):
        # 使用RSA私钥解密数据
        decrypted_data = rsa.decrypt(base64.b64decode(encrypted_data), self.private_key).decode()
        return decrypted_data

#全删掉
# if __name__ == '__main__':
#     # 要加密的数据
#     message = "com.area730.survival"
#     encrypted_data = RSA().encrypt(message)
#     print("加密后的数据：", encrypted_data)
#
#     decrypted_data = RSA().decrypt(encrypted_data)
#     print("解密后的数据：", decrypted_data)
#     print(decrypted_data == message)