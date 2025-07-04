build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

rebuild:
	docker-compose down
	docker-compose build
	docker-compose up -d
