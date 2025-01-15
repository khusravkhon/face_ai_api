build:
	docker build -t face_api .

run:
	docker run -p 5000:5000 face_api
