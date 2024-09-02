import time,math,random,os,re
import utils,constants,config
import pickle, hashlib
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.keys import Keys
from gpt import (get_keys_from_gpt_response, 
                 make_prompt, make_prompt2, 
                 remove_duplicates, make_prompt_radio,
                 make_prompt2_radio, ask_gpt,
                 message)

class Linkedin:
    def __init__(self):
            utils.prYellow("🌐 Bot will run in Chrome browser and log in Linkedin for you.")
            chrome_install = ChromeDriverManager().install()
            folder = os.path.dirname(chrome_install)
            chromedriver_path = os.path.join(folder, "chromedriver.exe")
            service = ChromeService(chromedriver_path)

            self.driver = webdriver.Chrome(service=service,options=utils.chromeBrowserOptions())
            self.cookies_path = f"{os.path.join(os.getcwd(),'cookies')}/{self.getHash(config.email)}.pkl"
            self.driver.get('https://www.linkedin.com')
            self.loadCookies()

            if not self.isLoggedIn():
                self.driver.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
                utils.prYellow("🔄 Trying to log in Linkedin...")
                try:    
                    self.driver.find_element("id","username").send_keys(config.email)
                    time.sleep(2)
                    self.driver.find_element("id","password").send_keys(config.password)
                    time.sleep(2)
                    self.driver.find_element("xpath",'//button[@type="submit"]').click()
                    time.sleep(30)
                except:
                    utils.prRed("❌ Couldn't log in Linkedin by using Chrome. Please check your Linkedin credentials on config files line 7 and 8.")

                self.saveCookies()
    
    def fill_answers_by_gpt(self):
        try:
                                    
            b=self.driver.find_elements(By.XPATH,'//*[contains(@class, "artdeco-text-input--label")]') # get box questions
            box_questions=[]
            for u in b: 
                box_questions.append(u.text)
                
            if box_questions!=[]:
                box_input_elements=self.driver.find_elements(By.XPATH,'//*[contains(@class, " artdeco-text-input--input")]') #box inputs
                
                for t in box_input_elements:
                    t.send_keys(Keys.CONTROL, 'a')
                    t.send_keys(Keys.DELETE)

                try:
                    self.driver.find_element(By.CSS_SELECTOR,
                            "button[aria-label='Continue to next step']").click() #click next to get error titles again
                except:
                    self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='Review your application']").click()

                b = self.driver.find_elements(By.XPATH,'//div[@class="artdeco-inline-feedback artdeco-inline-feedback--error ember-view mt1" and ancestor::div[@data-test-single-line-text-form-component]]') 

                box_options=[]
                for bo in b:
                    box_options.append(bo.text)

                final_box_questions=[]
                try:
                    for i in range(len(box_questions)):
                        final_box_questions.append(box_questions[i]+' .Answer this question in this format: '+ box_options[i])
                except IndexError:
                    final_box_questions=box_questions
                    pass
                
                if final_box_questions!=[]:
                    answer = ask_gpt(make_prompt(final_box_questions))
                    
                    final_answer = ask_gpt(make_prompt2(final_box_questions , answer))
                    final_box_answers = get_keys_from_gpt_response(final_answer)
                    message(f"Box Questions: {final_box_questions}, GPT answer : {final_box_answers}")

                    box_input_elements=self.driver.find_elements(By.XPATH,'//*[contains(@class, " artdeco-text-input--input")]') #box inputs
                    
                    for t in range(len(box_input_elements)):
                        box_input_elements[t].send_keys(final_box_answers[t])
                        time.sleep(0.1)
        except Exception as e:
            print(f"An error occurred: {e}")
            
        try:
            radio_element = self.driver.find_elements(By.XPATH,"//*[contains(@id, 'radio-button-form-component-formElement-urn-li-jobs-applyfor')]")                                                        

            radio_quesions=[]
            old_ele=None
            for r in radio_element:
                if r.text == old_ele:
                    continue
                r.text.split('\n')
                appp = ' '.join(remove_duplicates(r.text.split("\n")))
                if appp!="Please make a selection" and appp!='':
                    radio_quesions.append(appp)
                old_ele = r.text
            
            final_radio_questions = remove_duplicates(radio_quesions)
            
            if final_radio_questions!=[]:
                answer = ask_gpt(make_prompt_radio(final_radio_questions))
                final_answer = ask_gpt(make_prompt2_radio(final_radio_questions , answer))
                final_radio_answers = get_keys_from_gpt_response(final_answer)
                message(f"Radio Questions: {final_radio_questions}, GPT answer : {final_radio_answers}")
                all_answers_list =[]
                fieldsets = self.driver.find_elements(By.XPATH, '//fieldset[contains(@id, "radio-button-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-")]')
                for t in range(len(final_radio_answers)):
                    question = fieldsets[t].text
                    match = re.search("Required\n",question)
                    start,end = match.span()
                    answers = question[end:].split("\n")

                    elements = self.driver.find_elements(By.XPATH,f'//label[@data-test-text-selectable-option__label="{final_radio_answers[t]}"]')
                    e=all_answers_list.count(final_radio_answers[t])
                    if elements==[]:
                        elements = self.driver.find_elements(By.XPATH,f'//label[@data-test-text-selectable-option__label="{final_radio_answers[t][:-1]}"]')
                        e=all_answers_list.count(final_radio_answers[t])
                    elements[e].click()
                    all_answers_list.extend(answers)

        except Exception as e:
            print(f"An error occurred: {e}")

        try:
            
            drawdown_read = self.driver.find_elements(By.XPATH,"//*[contains(@for, 'text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement')]")
            drawdown_questions=[]
            
            for k in drawdown_read:
                drawdown_questions.append(k.text.split('\n')[1])
            if drawdown_questions!=[]:
                drawdown_options_e=self.driver.find_elements(By.XPATH,"//*[contains(@id, 'text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement')]")
                
                drawdown_options=[]
                for b in drawdown_options_e:
                    if b.text!='Please enter a valid answer':
                        drawdown_options.append(b.text)
                        
                final_drawdown_questions = []
                for i in range(len(drawdown_questions)):
                    final_drawdown_questions.append(drawdown_questions[i]+' '+drawdown_options[i])
                    
                answer = ask_gpt(make_prompt_radio(final_drawdown_questions))
                final_answer = ask_gpt(make_prompt2_radio(final_drawdown_questions , answer))
                final_drawdown_answers = get_keys_from_gpt_response(final_answer)
                message(f"Drawdown Questions: {final_drawdown_questions}, GPT answer : {final_drawdown_answers}")
                
                elements = self.driver.find_elements(By.XPATH,"//*[contains(@id, 'text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement')]")
                for trying in range(len(elements)):
                    try:
                        elements = self.driver.find_elements(By.XPATH,"//*[contains(@id, 'text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement')]")
                        for t in range(len(elements)):
                            from selenium.webdriver.support.ui import Select 
                            Select(elements[t]).select_by_visible_text(final_drawdown_answers[t])
                            time.sleep(0.5)
                    except:
                        pass
                    
        except Exception as e:
            print(f"An error occurred: {e}")

    def getHash(self, string):
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    def loadCookies(self):
        if os.path.exists(self.cookies_path):
            cookies =  pickle.load(open(self.cookies_path, "rb"))
            self.driver.delete_all_cookies()
            for cookie in cookies:
                self.driver.add_cookie(cookie)

    def saveCookies(self):
        pickle.dump(self.driver.get_cookies() , open(self.cookies_path,"wb"))
    
    def isLoggedIn(self):
        self.driver.get('https://www.linkedin.com/feed')
        try:
            self.driver.find_element(By.XPATH,'//*[@id="ember14"]')
            return True
        except:
            pass
        return False 
    
    def generateUrls(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        try: 
            with open('data/urlData.txt', 'w',encoding="utf-8" ) as file:
                linkedinJobLinks = utils.LinkedinUrlGenerate().generateUrlLinks()
                for url in linkedinJobLinks:
                    file.write(url+ "\n")
            utils.prGreen("✅ Apply urls are created successfully, now the bot will visit those urls.")
        except:
            utils.prRed("❌ Couldn't generate urls, make sure you have editted config file line 25-39")

    def esayapply(self, applied_job_ids, jobID):
        try:
            self.driver.find_element(By.CSS_SELECTOR,
                "button[aria-label='Submit application']").click()
            applied_job_ids.append(jobID)
            print("* Just Applied to this job!")
            time.sleep(5)
        except:
            try:
                ####Logic 1 start#######
                for g in range(5):
                    really_applied=False
                    try:
                        for i in range(10):
                            
                            self.driver.find_element(By.CSS_SELECTOR,
                                "button[aria-label='Continue to next step']").click() #click next
                            time.sleep(2)
                    except:
                        pass
                    try:
                        self.driver.find_element(By.CSS_SELECTOR,
                            "button[aria-label='Submit application']").click()
                        applied_job_ids.append(jobID)
                        really_applied=True
                        time.sleep(5)
                        break
                    except:
                        pass
                    try:
                        self.driver.find_element(By.CSS_SELECTOR,
                                "button[aria-label='Review your application']").click()
                    except:
                        pass
                    try:
                        self.driver.find_element(By.CSS_SELECTOR,
                            "button[aria-label='Submit application']").click()
                        applied_job_ids.append(jobID)
                        really_applied=True
                        time.sleep(5)
                        break
                    except:
                        pass
                    try:
                        self.fill_answers_by_gpt()
                        time.sleep(8)
                    except:
                        message("some error in filling ans by gpt")
                    
                    try:
                        self.driver.find_element(By.CSS_SELECTOR,
                                "button[aria-label='Review your application']").click()
                    except:
                        pass
                    try:
                        application_sent = self.driver.find_element(By.CSS_SELECTOR, ".artdeco-modal__header.ember-view").text 
                        if application_sent == 'Application sent':
                            really_applied=True
                            applied_job_ids.append(jobID)
                            break
                    except:
                        pass                                               
                    try:
                        self.driver.find_element(By.CSS_SELECTOR,
                            "button[aria-label='Submit application']").click()
                        really_applied=True
                        applied_job_ids.append(jobID)
                        time.sleep(5)
                        break
                    except:
                        pass
                    
                ####Logic 1 end#######
                
                if not really_applied:

                    percen = self.driver.find_element(By.XPATH,"/html/body/div[3]/div/div/div[2]/div/div/span").text
                    percen_numer = int(percen[0:percen.index("%")])
                    if int(percen_numer) < 25:
                        print("*More than 5 pages,wont apply to this job! Link: " +jobID)
                    elif int(percen_numer) < 30:
                        try:
                            self.driver.find_element(By.CSS_SELECTOR,
                            "button[aria-label='Continue to next step']").click()
                            time.sleep(random.randint(3,5))
                            self.driver.find_element(By.CSS_SELECTOR,
                            "button[aria-label='Continue to next step']").click()
                            time.sleep(random.randint(3,5))
                            self.driver.find_element(By.CSS_SELECTOR,
                            "button[aria-label='Review your application']").click()
                            time.sleep(random.randint(3,5))
                            self.driver.find_element(By.CSS_SELECTOR,
                            "button[aria-label='Submit application']").click()
                            applied_job_ids.append(jobID)
                            really_applied=True
                            print("* Just Applied to this job!")
                        except:
                            print("*4 Pages,wont apply to this job! Extra info needed. Link: " +jobID)
                    elif int(percen_numer) < 40:
                        try: 
                            self.driver.find_element(By.CSS_SELECTOR,
                            "button[aria-label='Continue to next step']").click()
                            time.sleep(random.randint(3,6))
                            self.driver.find_element(By.CSS_SELECTOR,
                            "button[aria-label='Review your application']").click()
                            time.sleep(random.randint(3,6))
                            self.driver.find_element(By.CSS_SELECTOR,
                            "button[aria-label='Submit application']").click()
                            applied_job_ids.append(jobID)
                            really_applied=True
                            print("* Just Applied to this job!")
                        except:
                            print("*3 Pages,wont apply to this job! Extra info needed. Link: " +jobID) 
                    elif int(percen_numer) < 60:
                        try:
                            self.driver.find_element(By.CSS_SELECTOR,
                            "button[aria-label='Review your application']").click()
                            time.sleep(random.randint(3,6))
                            self.driver.find_element(By.CSS_SELECTOR,
                            "button[aria-label='Submit application']").click()
                            applied_job_ids.append(jobID)
                            really_applied=True
                            print("* Just Applied to this job!")
                        except:
                            print("* 2 Pages,wont apply to this job! Unknown.  Link: " +jobID)
            
                if really_applied:
                    self.displayWriteResults(f"Application sent - jobID - {jobID}")
                else:
                    self.displayWriteResults(f"Application can not sent - jobID - {jobID}")
            except:
                message(f"Cannot apply to this Job: {jobID}")
                self.displayWriteResults(f"Application can not sent - jobID - {jobID}")

    def linkJobApply(self):
        self.generateUrls()
        countJobs = 0
        applied_job_ids=[]
        urlData = utils.getUrlDataFile()

        for url in urlData:        
            self.driver.get(url)
            time.sleep(random.uniform(1, constants.botSpeed))
            try:
                totalJobs = self.driver.find_element(By.XPATH,'//small').text 
            except NoSuchElementException:
                print("no small element found")
                continue
            
            totalPages = utils.jobsToPages(totalJobs)
            urlWords =  utils.urlToKeywords(url)
            lineToWrite = "\n Category: " + urlWords[0] + ", Location: " +urlWords[1] + ", Applying " +str(totalJobs)+ " jobs."
            self.displayWriteResults(lineToWrite)

            for page in range(totalPages):
                currentPageJobs = constants.jobsPerPage * page
                url = url +"&start="+ str(currentPageJobs)
                self.driver.get(url)

                time.sleep(random.uniform(1, constants.botSpeed))
                offersPerPage = self.driver.find_elements(By.XPATH, '//li[@data-occludable-job-id]')
                offerIds = [(offer.get_attribute(
                    "data-occludable-job-id").split(":")[-1]) for offer in offersPerPage]
                time.sleep(random.uniform(1, constants.botSpeed))

                for offer in offersPerPage:
                    if not self.element_exists(offer, By.XPATH, ".//*[contains(text(), 'Applied')]"):
                        offerId = offer.get_attribute("data-occludable-job-id")
                        offerIds.append(int(offerId.split(":")[-1]))
                # print("offerIds ", offerIds)
                
                for jobID in offerIds:
                    offerPage = 'https://www.linkedin.com/jobs/view/' + str(jobID)
                    self.driver.get(offerPage)
                    time.sleep(random.uniform(1, constants.botSpeed))

                    countJobs += 1

                    jobProperties = self.getJobProperties(countJobs)
                    if "blacklisted" in jobProperties: 
                        lineToWrite = jobProperties + " | " + "* 🤬 Blacklisted Job, skipped!: " +str(offerPage)
                        self.displayWriteResults(lineToWrite)
                    
                    else :                    
                        easyApplybutton = self.easyApplyButton()

                        if easyApplybutton is not False:
                            easyApplybutton.click()
                            self.esayapply(applied_job_ids,jobID)
                        else:
                            lineToWrite = jobProperties + " | " + "* 🥳 Already applied! Job: " +str(offerPage)
                            self.displayWriteResults(lineToWrite)

            self.displayWriteResults(f"Category: {urlWords[0]} , {urlWords[1]} applied: {str(len(applied_job_ids))} jobs out of {str(countJobs)}")

    def chooseResume(self):
        try:
            self.driver.find_element(
                By.CLASS_NAME, "jobs-document-upload__title--is-required")
            resumes = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'ui-attachment--pdf')]")
            if (len(resumes) == 1 and resumes[0].get_attribute("aria-label") == "Select this resume"):
                resumes[0].click()
            elif (len(resumes) > 1 and resumes[config.preferredCv-1].get_attribute("aria-label") == "Select this resume"):
                resumes[config.preferredCv-1].click()
            elif (type(len(resumes)) != int):
                utils.prRed(
                    "❌ No resume has been selected please add at least one resume to your Linkedin account.")
        except:
            pass

    def getJobProperties(self, count):
        textToWrite = ""
        jobTitle = ""
        jobLocation = ""

        try:
            jobTitle = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'job-title')]").get_attribute("innerHTML").strip()
            res = [blItem for blItem in config.blackListTitles if (blItem.lower() in jobTitle.lower())]
            if (len(res) > 0):
                jobTitle += "(blacklisted title: " + ' '.join(res) + ")"
        except Exception as e:
            if (config.displayWarnings):
                utils.prYellow("⚠️ Warning in getting jobTitle: " + str(e)[0:50])
            jobTitle = ""

        try:
            time.sleep(5)
            jobDetail = self.driver.find_element(By.XPATH, "//div[contains(@class, 'job-details-jobs')]//div").text.replace("·", "|")
            res = [blItem for blItem in config.blacklistCompanies if (blItem.lower() in jobTitle.lower())]
            if (len(res) > 0):
                jobDetail += "(blacklisted company: " + ' '.join(res) + ")"
        except Exception as e:
            if (config.displayWarnings):
                print(e)
                utils.prYellow("⚠️ Warning in getting jobDetail: " + str(e)[0:100])
            jobDetail = ""

        try:
            jobWorkStatusSpans = self.driver.find_elements(By.XPATH, "//span[contains(@class,'ui-label ui-label--accent-3 text-body-small')]//span[contains(@aria-hidden,'true')]")
            for span in jobWorkStatusSpans:
                jobLocation = jobLocation + " | " + span.text

        except Exception as e:
            if (config.displayWarnings):
                print(e)
                utils.prYellow("⚠️ Warning in getting jobLocation: " + str(e)[0:100])
            jobLocation = ""

        textToWrite = str(count) + " | " + jobTitle +" | " + jobDetail + jobLocation
        return textToWrite

    def easyApplyButton(self):
        try:
            time.sleep(random.uniform(1, constants.botSpeed))
            button = self.driver.find_element(By.XPATH, "//div[contains(@class,'jobs-apply-button--top-card')]//button[contains(@class, 'jobs-apply-button')]")
            EasyApplyButton = button
        except: 
            EasyApplyButton = False

        return EasyApplyButton

    def applyProcess(self, percentage, offerPage):
        applyPages = math.floor(100 / percentage) - 2 
        result = ""
        for pages in range(applyPages):  
            self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']").click()

        self.driver.find_element( By.CSS_SELECTOR, "button[aria-label='Review your application']").click()
        time.sleep(random.uniform(1, constants.botSpeed))

        if config.followCompanies is False:
            try:
                self.driver.find_element(By.CSS_SELECTOR, "label[for='follow-company-checkbox']").click()
            except:
                pass

        self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']").click()
        time.sleep(random.uniform(1, constants.botSpeed))

        result = "* 🥳 Just Applied to this job: " + str(offerPage)

        return result

    def displayWriteResults(self,lineToWrite: str):
        try:
            print(lineToWrite)
            utils.writeResults(lineToWrite)
        except Exception as e:
            utils.prRed("❌ Error in DisplayWriteResults: " +str(e))

    def element_exists(self, parent, by, selector):
        return len(parent.find_elements(by, selector)) > 0

start = time.time()
Linkedin().linkJobApply()
end = time.time()
utils.prYellow("---Took: " + str(round((time.time() - start)/60)) + " minute(s).")
