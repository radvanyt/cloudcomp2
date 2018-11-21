import connexion

def main():
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.add_api('swagger.yaml', arguments={'title': 'Swagger Petstore'})
    app.run(port=8080)

if __name__ == '__main__':
    main()