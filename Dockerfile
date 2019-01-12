FROM kennethreitz/pipenv
ENV PORT '8080'
COPY . /app
CMD python3 api.py
EXPOSE 8080
