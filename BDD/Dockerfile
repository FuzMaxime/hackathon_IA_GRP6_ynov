# Stage 1 — validation des scripts SQL
FROM alpine:3.20 AS sql-prep

WORKDIR /sql
COPY *.sql ./

RUN apk add --no-cache grep \
  && test -f 01_schema.sql \
  && grep -q "CREATE TABLE" 01_schema.sql

# Stage 2 — image MySQL avec init automatique
FROM mysql:8.4

LABEL maintainer="TechCorp GRP6"
LABEL description="MySQL pour utilisateurs et historique de conversations"

COPY --from=sql-prep /sql /docker-entrypoint-initdb.d/

EXPOSE 3306
