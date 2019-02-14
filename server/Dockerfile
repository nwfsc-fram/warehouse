# Simple Dockerfile to build an image which Warehouse can be installed in to
#
# Based on: https://github.com/CentOS/CentOS-Dockerfiles/blob/master/httpd/centos6/Dockerfile
# "ported" by Adam Miller <maxamillion@fedoraproject.org> from
#   https://github.com/fedora-cloud/Fedora-Dockerfiles
#
# Originally written for Fedora-Dockerfiles by
#   "Scott Collier" <scollier@redhat.com>

FROM centos:centos6
MAINTAINER The CentOS Project <cloud-ops@centos.org>

RUN yum -y update; yum clean all
RUN yum -y install httpd; yum clean all

EXPOSE 80

# Simple startup script to avoid some issues observed with container restart
ADD ./deploy/run-httpd.sh /run-httpd.sh
RUN chmod -v +x /run-httpd.sh

CMD ["/run-httpd.sh"]

# install EFH-Catalog content
COPY ./app/efh-catalog /var/www/html/app-warehouse/efh-catalog
RUN chmod -R o+rx /var/www/html/app-warehouse
COPY ./deploy/httpd/conf.d/wsgi-warehouse.conf /etc/httpd/conf.d/
#FIXME: comment out mod_wsgi components, as this Dockerfile does not yet include that module.
RUN sed -i 's/^WSGIPythonPath /#WSGIPythonPath /' /etc/httpd/conf.d/wsgi-warehouse.conf
RUN sed -i 's/^    Alias /#    Alias /' /etc/httpd/conf.d/wsgi-warehouse.conf
