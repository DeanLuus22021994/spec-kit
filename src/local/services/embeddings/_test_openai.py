from semantic.embeddings.main import generate_embedding_with_openai, generate_embeddings_batch_with_openai

print(
    "single len",
    len(generate_embedding_with_openai("test", "text-embedding-3-small")[0]),
)
print(
    "batch len",
    len(generate_embeddings_batch_with_openai(["a", "b"], "text-embedding-3-small")[0]),
)
