import time
import traceback
from typing import List, Dict, Any, Generator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SIMULADOR_URL = "https://simulador.b3.com.br/"

class B3SimulatorBot:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None

    def start_driver(self):
        chrome_options = webdriver.ChromeOptions()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--start-maximized")
        # Suppress logging
        chrome_options.add_argument("--log-level=3")
        
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def close_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _positive_int(self, val):
        """Convert value to positive integer (assumes sign already handled)"""
        try:
            return int(abs(val))
        except:
            try:
                return int(abs(float(val)))
            except:
                return 0

    def _selecionar_opcao_sobre_acao(self):
        xp = "//label[contains(., 'Opção sobre Ação')]"
        try:
            elem = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, xp))
            )
            self.driver.execute_script("arguments[0].click();", elem)
            time.sleep(0.2)
        except Exception as e:
            # Maybe it's already selected or different layout, log warning but continue
            pass

    def _preencher_codigo(self, ativo):
        caixa = WebDriverWait(self.driver, 8).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="symbolSelect"]/div'))
        )
        caixa.click()
        time.sleep(0.5)
        input_real = caixa.find_element(By.TAG_NAME, "input")
        input_real.clear()
        input_real.send_keys(ativo)
        time.sleep(0.5)
        input_real.send_keys(Keys.ENTER)
        time.sleep(0.8)

    def _preencher_quantidade_compra(self, qtd):
        time.sleep(0.5)
        try:
            campo = WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="qtd_buy"]'))
            )
            # Try JavaScript first (more reliable in server environments)
            self.driver.execute_script("arguments[0].value = arguments[1];", campo, str(qtd))
            time.sleep(0.3)
        except Exception as e:
            # Fallback to normal method
            campo = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="qtd_buy"]'))
            )
            campo.click()
            time.sleep(0.2)
            campo.clear()
            campo.send_keys(str(qtd))
            time.sleep(0.2)

    def _preencher_quantidade_venda(self, qtd):
        time.sleep(0.5)
        try:
            div = WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="divQtdSell"]'))
            )
            input_real = div.find_element(By.TAG_NAME, "input")
            # Try JavaScript first (more reliable in server environments)
            self.driver.execute_script("arguments[0].value = arguments[1];", input_real, str(qtd))
            time.sleep(0.3)
        except Exception as e:
            # Fallback to normal method
            div = WebDriverWait(self.driver, 8).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="divQtdSell"]'))
            )
            input_real = div.find_element(By.TAG_NAME, "input")
            input_real.click()
            time.sleep(0.2)
            input_real.clear()
            input_real.send_keys(str(qtd))
            time.sleep(0.2)

    def _clicar_adicionar(self):
        xpaths = [
            "//button[contains(., 'ADICIONAR')]",
            "//button[contains(., 'Adicionar')]",
            "//button[normalize-space()='ADICIONAR']",
            "//button[contains(@class, 'btn') and contains(., 'ADICIONAR')]"
        ]
        for xp in xpaths:
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.2)
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
                return True
            except:
                continue
        return False

    def _clicar_calcular(self):
        try:
            wait = WebDriverWait(self.driver, 5)
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
                self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(0.2)
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(1.5)
                return True
            else:
                return False
        except Exception:
            return False

    def _capturar_resultado(self):
        try:
            xp_resultado = "//*[contains(text(), 'Risco das Posições')]/following-sibling::*"
            elem = WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.XPATH, xp_resultado))
            )
            texto = elem.text.strip()
            texto_limpo = texto.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
            if not texto_limpo or texto_limpo == "-":
                return 0.0
            return float(texto_limpo)
        except Exception:
            return 0.0

    def _close_modals(self):
        # Try to close generic modals if they appear
        try:
            # Example: cookie consent or welcome modal
            # This is a placeholder as specific modal XPaths weren't provided, 
            # but good to have a hook.
            pass
        except:
            pass

    def process_simulation(self, positions: List[Dict[str, Any]]) -> Generator[Dict[str, Any], None, None]:
        """
        Generator that yields log messages and final result.
        positions: List of dicts with 'asset', 'quantity', 'type'
        """
        try:
            yield {"type": "log", "message": "Iniciando driver do Chrome...", "level": "info"}
            self.start_driver()
            
            total_batches = (len(positions) + 19) // 20
            yield {"type": "log", "message": f"Total de posições: {len(positions)}. Lotes: {total_batches}", "level": "info"}
            
            accumulated_risk = 0.0
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * 20
                end_idx = min((batch_idx + 1) * 20, len(positions))
                batch = positions[start_idx:end_idx]
                
                yield {"type": "log", "message": f"Processando lote {batch_idx + 1}/{total_batches}...", "level": "info"}
                
                try:
                    self.driver.get(SIMULADOR_URL)
                    time.sleep(1.5) # Wait for load
                    self._close_modals()
                    
                    self._selecionar_opcao_sobre_acao()
                    
                    for pos in batch:
                        ativo = pos['asset'].strip()
                        qtd = self._positive_int(pos['quantity'])
                        tipo = pos.get('type', 'Compra') # Default to Compra if missing
                        
                        yield {"type": "log", "message": f"Adicionando: {ativo} ({tipo} {qtd})", "level": "info"}
                        
                        try:
                            self._preencher_codigo(ativo)
                            
                            if tipo == "Compra":
                                self._preencher_quantidade_compra(qtd)
                                self._preencher_quantidade_venda(0)
                            else:
                                self._preencher_quantidade_venda(qtd)
                                self._preencher_quantidade_compra(0)
                                
                            if self._clicar_adicionar():
                                yield {"type": "progress", "value": 1}
                            else:
                                yield {"type": "log", "message": f"Falha ao adicionar {ativo}", "level": "warning"}
                        except Exception as e:
                             yield {"type": "log", "message": f"Erro ao adicionar {ativo}: {str(e)}", "level": "warning"}
                        
                        time.sleep(0.2)
                    
                    yield {"type": "log", "message": "Calculando risco do lote...", "level": "info"}
                    self._clicar_calcular()
                    
                    risk = self._capturar_resultado()
                    accumulated_risk += risk
                    yield {"type": "log", "message": f"Risco do lote {batch_idx + 1}: R$ {risk:,.2f}", "level": "success"}
                    
                except Exception as e:
                    yield {"type": "log", "message": f"Erro no lote {batch_idx + 1}: {str(e)}", "level": "error"}
                    traceback.print_exc()

            result_data = {
                "risk": accumulated_risk,
                "date": time.strftime("%d/%m/%Y %H:%M:%S")
            }
            yield {"type": "result", "data": result_data}
            yield {"type": "log", "message": "Simulação finalizada com sucesso.", "level": "success"}

        except Exception as e:
            yield {"type": "log", "message": f"Erro fatal: {str(e)}", "level": "error"}
        finally:
            self.close_driver()
