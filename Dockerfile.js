# Frontend Dockerfile for JS App (Development)
# Use PixelArch Quartz as base image (already has yay installed)
FROM lunamidori5/pixelarch:quartz

# Update OS release info
RUN sudo sed -i 's/Quartz/Bun-Server/g' /etc/os-release

# Update system and install curl
RUN yay -Syu --noconfirm curl && yay -Yccc --noconfirm

# Install wget
RUN yay -Syu --noconfirm wget && yay -Yccc --noconfirm

# Install git
RUN yay -Syu --noconfirm git && yay -Yccc --noconfirm

# Install base-devel
RUN yay -Syu --noconfirm base-devel && yay -Yccc --noconfirm

# Install nodejs
RUN yay -Syu --noconfirm nodejs && yay -Yccc --noconfirm

# Install npm
RUN yay -Syu --noconfirm npm && yay -Yccc --noconfirm

# Install unzip
RUN yay -Syu --noconfirm unzip && yay -Yccc --noconfirm

# Install Bun.js
RUN yay -S --noconfirm bun && yay -Yccc --noconfirm

WORKDIR /app
EXPOSE 59001
# Source will be bind-mounted at runtime; install deps in entrypoint
CMD ["bash", "-lc", "bash /app/docker-entrypoint.sh"]
