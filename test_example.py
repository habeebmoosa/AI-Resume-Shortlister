try:
    from langchain.prompts import PromptTemplate
    print("LangChain imported successfully!")
except ModuleNotFoundError as e:
    print(e)
