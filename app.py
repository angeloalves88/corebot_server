from application import create_app

app = create_app()

if __name__ == '__main__':
    if app is None:
        print("Erro: Não foi possível criar a aplicação! ")
    else:
        app.run(host='0.0.0.0', port=5010, debug=True)
