#install docker
sudo apt install docker.io docker-compose


#register docekr
sudo systemctl enable --now docker docker.socket containerd



#create network docker
sudo docker network create --driver bridge my-network


#conteiner postgres
sudo docker run --name my-postgres-container --network=my-network -p 5433:5432 -e POSTGRES_PASSWORD=postgres -d postgres


#conteiner pgadmin
sudo docker run --name my-pgadmin-container --network=my-network -p 15432:80 -e PGADMIN_DEFAULT_EMAIL=postgres@gmail.com -e PGADMIN_DEFAULT_PASSWORD=postgres -d dpage/pgadmin4

#conteiner rabbitmq 
sudo docker run --name my-rabbitmq-container -d -p 5672:5672 rabbitmq

#install requiriments
pip install -r requirements.txt

#docker compose 2
https://docs.docker.com/compose/install/linux/#install-the-plugin-manually

#docker up
docker compose up -d --build

#docker logs 
docker compose logs django -f