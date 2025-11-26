variable "REGISTRY" {
  default = "localhost:5000/spec-kit"
}

variable "VERSION" {
  default = "latest"
}

group "default" {
  targets = ["redis", "database", "embeddings", "face-matcher", "vector"]
}

target "redis" {
  context = "services/redis"
  dockerfile = "Dockerfile"
  tags = ["${REGISTRY}/redis:${VERSION}"]
  cache-from = ["type=local,src=.buildx-cache/redis"]
  cache-to = ["type=local,dest=.buildx-cache/redis,mode=max"]
}

target "database" {
  context = "services/database"
  dockerfile = "Dockerfile"
  tags = ["${REGISTRY}/database:${VERSION}"]
  cache-from = ["type=local,src=.buildx-cache/database"]
  cache-to = ["type=local,dest=.buildx-cache/database,mode=max"]
}

target "embeddings" {
  context = "services/embeddings"
  dockerfile = "Dockerfile"
  tags = ["${REGISTRY}/embeddings:${VERSION}"]
  cache-from = ["type=local,src=.buildx-cache/embeddings"]
  cache-to = ["type=local,dest=.buildx-cache/embeddings,mode=max"]
}

target "face-matcher" {
  context = "services/face-matcher"
  dockerfile = "Dockerfile"
  tags = ["${REGISTRY}/face-matcher:${VERSION}"]
  cache-from = ["type=local,src=.buildx-cache/face-matcher"]
  cache-to = ["type=local,dest=.buildx-cache/face-matcher,mode=max"]
}

target "vector" {
  context = "services/vector"
  dockerfile = "Dockerfile"
  tags = ["${REGISTRY}/vector:${VERSION}"]
  cache-from = ["type=local,src=.buildx-cache/vector"]
  cache-to = ["type=local,dest=.buildx-cache/vector,mode=max"]
}
