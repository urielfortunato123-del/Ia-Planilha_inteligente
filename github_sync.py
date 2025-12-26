import os
from git import Repo
from dotenv import load_dotenv

load_dotenv()

def sync_to_github():
    repo_path = os.getcwd()
    github_url = os.getenv("GITHUB_REPO_URL")
    github_token = os.getenv("GITHUB_TOKEN")
    
    if not github_url:
        print("Erro: GITHUB_REPO_URL não configurado no arquivo .env")
        return

    try:
        # Initialize repo if not already
        if not os.path.exists(os.path.join(repo_path, ".git")):
            repo = Repo.init(repo_path)
            print("Repositório inicializado.")
        else:
            repo = Repo(repo_path)

        # Configure remote
        if "origin" in repo.remotes:
            origin = repo.remote("origin")
        else:
            origin = repo.create_remote("origin", github_url)

        # Add and commit
        repo.git.add(A=True)
        repo.index.commit("Atualização automática da Planilha Inteligente")
        
        # Push
        origin.push(refspec='main:main')
        print("Sincronização com GitHub concluída com sucesso!")

    except Exception as e:
        print(f"Erro durante a sincronização: {e}")

if __name__ == "__main__":
    sync_to_github()
