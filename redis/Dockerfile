FROM redis:7

ARG REDIS_PASSWORD

RUN mkdir -p /usr/local/etc/redis
RUN echo "requirepass $REDIS_PASSWORD" > /usr/local/etc/redis/redis.conf

# Command to run the Redis server with the specified configuration file
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
