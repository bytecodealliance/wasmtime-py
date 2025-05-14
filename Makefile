start:
	docker-compose up -d
test:
	docker-compose exec -it app pytest
hello-world:
	docker-compose exec -it app python examples/hello.py
exec:
	docker-compose exec -it app bash
stop:
	docker-compose down
