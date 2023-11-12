class TokenGenerator:
    TOKEN_LENGTH = "0011"
    TOKEN_COUNTER = 0

    @staticmethod
    def generate_token():
        length = int(TokenGenerator.TOKEN_LENGTH, 2)
        TokenGenerator.TOKEN_COUNTER = TokenGenerator.TOKEN_COUNTER % (length + 1)
        token = format(TokenGenerator.TOKEN_COUNTER, f'0{length}b')
        TokenGenerator.TOKEN_COUNTER += 1
        return token