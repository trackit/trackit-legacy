FROM nginx:stable-alpine

# Setup exposed ports
EXPOSE 80

# Installing npm as grunt is needed to build the production version of the app
RUN apk update && apk add nodejs git python build-base

# To make sure the node binary is found
#RUN ln -s /usr/bin/nodejs /usr/bin/node

# Setup bower and grunt

RUN npm install -g grunt-cli
RUN npm install -g bower
RUN echo '{ "allow_root": true, "interactive": false }' > /root/.bowerrc

# Setup directory

RUN mkdir /trackit
WORKDIR /trackit

COPY ./ui/bower.json ./ui/.bowerrc ./
RUN bower install

COPY ./ui/package.json ./
RUN npm install

# Add remaining files
COPY ./ui/ ./

# Build project
RUN grunt prod

RUN cp -rv ./app/* /usr/share/nginx/html

ENV TRACKIT_DOMAIN=localhost
ENV API_TRACKIT_DOMAIN=http://localhost/api
ENV NOT_FOUND_URL=/#/login
CMD ./server.sh
