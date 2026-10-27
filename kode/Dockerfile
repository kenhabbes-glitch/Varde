# Plattformkjernen som container, for Cloud Run, Azure Container Apps, Fly.io eller egen server.
# Må kjøre kontinuerlig (minst én instans alltid på), ellers oppdages ikke stillhet.
FROM node:22-alpine
WORKDIR /app
COPY package.json ./
COPY shared ./shared
COPY platform ./platform
COPY dashboard ./dashboard
ENV PORT=8080 GVT_DATA=/data/data.json GVT_KEY=/data/platform-key.pem
RUN mkdir /data && chown node /data
USER node
EXPOSE 8080
# GVT_ADMIN_TOKEN og GVT_OPERATOR_TOKEN må settes som hemmeligheter i tjenesten. Uten dem stopper containeren.
CMD ["node", "platform/server.ts"]
