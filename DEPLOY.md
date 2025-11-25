# 🚀 Como Fazer Deploy no Render

## Pré-requisitos
1. Conta no [GitHub](https://github.com)
2. Conta no [Render](https://render.com)

## Passo a Passo

### 1️⃣ Criar Repositório no GitHub

1. Vá para [GitHub](https://github.com) e faça login
2. Clique em **"New repository"** (ou **"Novo repositório"**)
3. Dê um nome (ex: `b3-simulator`)
4. Escolha **Público** ou **Privado**
5. **NÃO** marque "Add a README file"
6. Clique em **"Create repository"**

### 2️⃣ Subir o Código para o GitHub

Abra o terminal/PowerShell na pasta `c:\Users\igorl\Downloads\app` e execute:

```bash
# Inicializar repositório Git
git init

# Adicionar todos os arquivos
git add .

# Fazer commit
git commit -m "Initial commit - B3 Simulator"

# Adicionar o repositório remoto (substitua SEU_USUARIO e SEU_REPOSITORIO)
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git

# Enviar para o GitHub
git branch -M main
git push -u origin main
```

### 3️⃣ Fazer Deploy no Render

1. Acesse [Render Dashboard](https://dashboard.render.com/)
2. Clique em **"New +"** → **"Web Service"**
3. Conecte sua conta do GitHub (se ainda não conectou)
4. Selecione o repositório que você criou
5. Configure:
   - **Name**: `b3-simulator` (ou qualquer nome)
   - **Environment**: **Docker**
   - **Plan**: **Free**
6. Clique em **"Create Web Service"**

### 4️⃣ Aguardar Deploy

- O Render vai automaticamente:
  - Detectar o `Dockerfile`
  - Instalar Chrome e dependências
  - Fazer build da imagem Docker
  - Iniciar o aplicativo

⏱️ **Tempo estimado**: 5-10 minutos

### 5️⃣ Acessar o App

Após o deploy, você receberá uma URL tipo:
```
https://b3-simulator.onrender.com
```

## ⚠️ Limitações do Plano Free

- **Cold Start**: Se não houver acesso por 15 minutos, o servidor "dorme" e leva ~30s para acordar
- **RAM**: 512MB (pode ser insuficiente para muitos ativos)
- **CPU**: Compartilhada
- **Horas**: 750 horas/mês grátis

## 🔄 Atualizações Futuras

Para atualizar o app:
```bash
git add .
git commit -m "Descrição da mudança"
git push
```

O Render fará deploy automático! 🎉

## 🆘 Problemas Comuns

### Erro de Memória
Se o app crashar com muitos ativos, considere:
- Upgrade para plano pago ($7/mês)
- Processar menos ativos por vez

### App não inicia
- Verifique os logs no Render Dashboard
- Certifique-se que todos os arquivos foram enviados ao GitHub

## 📞 Suporte

Se tiver problemas, verifique:
1. Logs no Render Dashboard
2. Se o GitHub está atualizado
3. Se o `Dockerfile` está correto
