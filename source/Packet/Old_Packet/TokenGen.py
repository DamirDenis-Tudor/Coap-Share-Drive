from source.Packet.Old_Packet.Config import TOKEN_LENGTH


class TokenGenerator:
    TOKEN_COUNTER = 0

    @staticmethod
    def generate_token():
        token_length = int(TOKEN_LENGTH, 2)

        max_token = 2**token_length - 1

        TokenGenerator.TOKEN_COUNTER = TokenGenerator.TOKEN_COUNTER % (max_token + 1)

        tkn = format(TokenGenerator.TOKEN_COUNTER, f'0{token_length}b')

        TokenGenerator.TOKEN_COUNTER += 1
        return tkn
