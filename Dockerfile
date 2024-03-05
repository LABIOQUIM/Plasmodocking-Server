# Usar uma imagem oficial do Python como imagem base
FROM python:3.9

# Definir o diretório de trabalho no contêiner
WORKDIR /var/www/server

# Copiar o arquivo de dependências e instalar as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante dos arquivos do projeto para o contêiner
COPY . .

# Comando para rodar a aplicação utilizando o servidor de desenvolvimento embutido do Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
