import json
import time
import asyncio
import traceback
from typing import List, Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Position(BaseModel):
    id: str
    asset: str
    quantity: float = 0
    type: str

    # Handle potential string/number mismatch from frontend if needed, 
    # but standard Pydantic types should work. 
    # The frontend sends 'quantity' as number.

class SimulationRequest(BaseModel):
    positions: List[Position]
    headless: bool

SIMULADOR_URL = "https://simulador.b3.com.br/"

def positive_int(val):
    try:
        return abs(int(val))
    except:
        return abs(int(float(val)))

def selecionar_opcao_sobre_acao(driver):
    xp = "//label[contains(., 'Opção sobre Ação')]"
    elem = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, xp))
    )
    driver.execute_script("arguments[0].click();", elem)
    time.sleep(0.5)

def preencher_codigo(driver, ativo):
    caixa = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="symbolSelect"]/div'))
    )
    caixa.click()
    time.sleep(0.5)
    input_real = caixa.find_element(By.TAG_NAME, "input")
    input_real.clear()
    input_real.send_keys(ativo)
    time.sleep(0.5)
    input_real.send_keys(Keys.ENTER)
    time.sleep(0.5)

def preencher_quantidade_compra(driver, qtd):
    campo = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="qtd_buy"]'))
    )
    campo.click()
    campo.clear()
    campo.send_keys(str(qtd))
    time.sleep(0.2)
    campo.send_keys(Keys.TAB)
    time.sleep(0.2)

def preencher_quantidade_venda(driver, qtd):
    div = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="divQtdSell"]'))
    )
    input_real = div.find_element(By.TAG_NAME, "input")
    input_real.click()
    input_real.clear()
    input_real.send_keys(str(qtd))
    time.sleep(0.2)
    input_real.send_keys(Keys.TAB)
    time.sleep(0.2)

def clicar_adicionar(driver):
    xpaths = [
        "//button[contains(., 'ADICIONAR')]",
        "//button[contains(., 'Adicionar')]",
        "//button[normalize-space()='ADICIONAR']",
        "//button[contains(@class, 'btn') and contains(., 'ADICIONAR')]"
    ]
    for xp in xpaths:
        try:
            btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(1)
            return True
        except:
            continue
    return False

def clicar_calcular(driver):
    try:
        wait = WebDriverWait(driver, 10)
        xpaths = [
            "//button[contains(., 'CALCULAR')]",
            "//button[contains(., 'Calcular')]",
            "//button[normalize-space()='CALCULAR']"
        ]
        btn = None
        for xp in xpaths:
            try:
                btn = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                break
            except:
                continue
        if btn:
            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(5)
            return True
        else:
            return False
    except Exception:
        return False

def capturar_resultado(driver):
    try:
        xp_resultado = "//*[contains(text(), 'Risco das Posições')]/following-sibling::*"
        elem = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.XPATH, xp_resultado))
        )
        texto = elem.text.strip()
        texto_limpo = texto.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
        if not texto_limpo or texto_limpo == "-":
            return 0.0
        return float(texto_limpo)
    except Exception:
        return 0.0

def process_simulation(positions: List[Position], headless: bool):
    # Generator to stream logs and results
    driver = None
    try:
        yield json.dumps({"type": "log", "message": "Iniciando driver do Chrome...", "level": "info"}) + "\n"
        
        chrome_options = webdriver.ChromeOptions()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--start-maximized")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        total_batches = (len(positions) + 19) // 20
        yield json.dumps({"type": "log", "message": f"Total de posições: {len(positions)}. Lotes: {total_batches}", "level": "info"}) + "\n"
        
        accumulated_risk = 0.0
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * 20
            end_idx = min((batch_idx + 1) * 20, len(positions))
            batch = positions[start_idx:end_idx]
            
            yield json.dumps({"type": "log", "message": f"Processando lote {batch_idx + 1}/{total_batches}...", "level": "info"}) + "\n"
            
            try:
                driver.get(SIMULADOR_URL)
                time.sleep(5) # Wait for load
                
                selecionar_opcao_sobre_acao(driver)
                
                for pos in batch:
                    ativo = pos.asset.strip()
                    qtd = positive_int(pos.quantity)
                    tipo = pos.type # 'Compra' or 'Venda'
                    
                    yield json.dumps({"type": "log", "message": f"Adicionando: {ativo} ({tipo} {qtd})", "level": "info"}) + "\n"
                    
                    preencher_codigo(driver, ativo)
                    
                    if tipo == "Compra":
                        preencher_quantidade_compra(driver, qtd)
                        preencher_quantidade_venda(driver, 0)
                    else:
                        preencher_quantidade_venda(driver, qtd)
                        preencher_quantidade_compra(driver, 0)
                        
                    if clicar_adicionar(driver):
                        yield json.dumps({"type": "progress", "value": 1}) + "\n"
                    else:
                        yield json.dumps({"type": "log", "message": f"Falha ao adicionar {ativo}", "level": "warning"}) + "\n"
                    
                    time.sleep(1)
                
                yield json.dumps({"type": "log", "message": "Calculando risco do lote...", "level": "info"}) + "\n"
                clicar_calcular(driver)
                
                risk = capturar_resultado(driver)
                accumulated_risk += risk
                yield json.dumps({"type": "log", "message": f"Risco do lote {batch_idx + 1}: R$ {risk:.2f}", "level": "success"}) + "\n"
                
            except Exception as e:
                yield json.dumps({"type": "log", "message": f"Erro no lote {batch_idx + 1}: {str(e)}", "level": "error"}) + "\n"
                traceback.print_exc()

        # Final Result
        result_data = {
            "risk": accumulated_risk,
            "guarantees": 0, # Not captured in script
            "balance": 0,    # Not captured in script
            "calculationTime": "N/A",
            "date": time.strftime("%d/%m/%Y %H:%M:%S")
        }
        yield json.dumps({"type": "result", "data": result_data}) + "\n"
        yield json.dumps({"type": "log", "message": "Simulação finalizada com sucesso.", "level": "success"}) + "\n"

    except Exception as e:
        yield json.dumps({"type": "log", "message": f"Erro fatal: {str(e)}", "level": "error"}) + "\n"
    finally:
        if driver:
            driver.quit()

@app.post("/simulate")
async def simulate(request: SimulationRequest):
    return StreamingResponse(
        process_simulation(request.positions, request.headless),
        media_type="application/x-ndjson"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
