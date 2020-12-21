
FROM rasa/rasa-sdk:2.1.2

WORKDIR /app

COPY actions /app/actions

USER root

RUN pip install --no-cache-dir -r actions/requirements.txt

USER 1001

CMD ["start", "--actions", "actions", "--debug"]
