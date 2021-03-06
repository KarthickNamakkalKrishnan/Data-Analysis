class population_comp:
    
    def __init__(self,SSN,claim_history):
        #initialisation of local variables
        self.SSN = SSN
        cursor.execute("select * from ISSWRK.KD_Claim_Duration_PREV_CLAIMS WHERE Q_DAY_ACM_CLM <> 0 AND ICD10 IS NOT NULL AND C_PDT = 'STD' AND D_THRU_APPROVED IS NOT NULL AND SSN=?",(self.SSN))
        self.claim_history = claim_history
        self.claim_history[self.SSN] = []
        self.Claim_count = 0
        self.exceeding_count = 0
        
    def gen_func(self):
        # generator function to get the arguments from cursor
        for i in cursor:
            yield i[5],i[7],i[8],i[17],i[15]
            
    def duration(self):
        try: # try catch block to exit the generator iteration
            while True:
                self.ICD9,self.type,self.MEDICAL_CODE,self.paid_dur,self.elm_per = next(self.gen_func())
                self.MEDICAL_CODE = str(self.MEDICAL_CODE.strip()) #striping white spaces
                self.ICD9 = str(self.ICD9.strip())
                self.ICD9 = self.ICD9.upper() 
                self.ill_dur = self.paid_dur + self.elm_per
                if ((self.type == 9) and (self.ICD9 != '724.6') and (self.ICD9 != '996.78')):
                    # ICD 9 mapping to ICD 10 mapping
                    self.MEDICAL_CODE = [str(ICD9_to_10['ICD10'][counter]) for counter,value in enumerate(ICD9_to_10['ICD9']) if value == self.ICD9][0]
                    self.MD_population = self.get_MD_pop() # API call
                    if type(self.MD_population) is int: # incrementing counter only if the return type is integer(for valid ICD)
                        self.Claim_count = self.Claim_count + 1
                        if self.ill_dur > self.MD_population:
                            self.exceeding_count = self.exceeding_count + 1
                elif (self.type == 10):
                    self.MD_population = self.get_MD_pop() # API call
                    if type(self.MD_population) is int: ## incrementing counter only if the return type is integer(for valid ICD)
                        self.Claim_count = self.Claim_count + 1
                        if self.ill_dur > self.MD_population:
                            self.exceeding_count = self.exceeding_count + 1
                        
        except StopIteration:
            if self.Claim_count > 0:
                self.claim_history[self.SSN].append({
                    'Total_claim': self.Claim_count,
                    'percentage_went_ab_median':(self.exceeding_count / self.Claim_count) * 100
                })
            #print(self.claim_history)
            pass
        
    def get_MD_pop(self):
        try:
            arg_string = f'{self.MEDICAL_CODE}'
            req = ur.Request("https://api.mdguidelines.com/api/v1/durations/population/" + arg_string,
                 headers={"RG-LICENSE-KEY":"f7722436-9fdc-4823-b617-303a0031019d"})
            resp_new = ur.urlopen(req).read()
            try:
                json_req = json.loads(resp_new)
                return json_req['MedianDurationInDays']
            except ValueError:
                pass
        except urllib.error.HTTPError as err:
            if err.code == 406:
                print('Error ICD code: {}'.format(self.MEDICAL_CODE))
            if err.code == 404:
                print('Error ICD code: {}'.format(self.MEDICAL_CODE))