from atproto import Client, client_utils
import password

def main():
    client = Client()
    profile = client.login('foleelli@oregonstate.edu', password.password)
    print('Welcome,', profile.display_name)
    
    #text = client_utils.TextBuilder().text('Hello World from ').link('Python SDK', 'https://atproto.blue')
    #post = client.send_post(text)
    #client.like(post.uri, post.cid)


if __name__ == '__main__':
    main()


