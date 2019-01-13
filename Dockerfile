FROM kennethreitz/pipenv
RUN apt-get update && apt-get install -y vim
ENV PORT '8080'
COPY . /app
CMD ["python3", "-u", "api.py"]
EXPOSE 8080
