# Usar una imagen base de Node
FROM node:18

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar package.json y package-lock.json
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar el resto del código
COPY . .

# Exponer el puerto 3000
EXPOSE 3000

# Configurar el servidor para escuchar en todas las interfaces
ENV HOST=0.0.0.0

# Iniciar el servidor de desarrollo
CMD ["npm", "start"]