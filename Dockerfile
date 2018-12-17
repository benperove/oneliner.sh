FROM kennethreitz/pipenv
ENV PORT '80'
COPY . /app
CMD python3 api.py
EXPOSE 80
