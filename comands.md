#create network docker
sudo docker network create --driver bridge my-network


#conteiner postgres
sudo docker run --name my-postgres-container --network=my-network -p 5433:5432 -e POSTGRES_PASSWORD=postgres -d postgres


#conteiner pgadmin
sudo docker run --name my-pgadmin-container --network=my-network -p 15432:80 -e PGADMIN_DEFAULT_EMAIL=postgres@gmail.com  PGADMIN_DEFAULT_PASSWORD=postgres -d dpage/pgadmin4


#conteiner rabbitmq 
sudo docker run -d -p 5672:5672 rabbitmq