��    �      d    �      �  g  �  R  I  L  �  x  �  ]  b  W  �           3     T     i      ~     �     �     �  L   �  E   ?  O   �     �     �     �     �           	          %     .     B     I     R     f  H   w     �     �      �          
       '   '  5   O     �     �  	   �     �     �  
   �  
   �     �     �  .        0     <     I     O     d     p     �  I   �     �     �     �            	   !     +     @  +   U  0   �  C   �  e   �  T   \  Y   �  &      Y   2   %   �   "   �      �      �      �   /   �   0   !  A   D!  Q   �!     �!     �!     �!     �!     
"     #"     ("     ."     ;"     ?"  	   H"     R"     d"     u"     �"     �"     �"     �"     �"     �"     �"     �"  	   �"     �"     �"     �"  A   #  +   J#     v#  
   �#  �  �#  ]   ]%     �%     �%     �%     �%     �%  >   �%     &&     .&     7&     F&     V&     ^&     g&     n&     t&     z&  
   �&     �&     �&     �&  K   �&  	   '     '     1'     F'     \'  	   e'  h   o'  }   �'     V(  '   f(     �(  I   �(  
   �(     �(     	)     ))     9)     K)     S)     c)  
   g)     r)     )  
   �)     �)  
   �)     �)     �)     �)     �)     �)      *  
   *     *     '*     7*     O*  
   R*     ]*     f*     m*     �*  .   �*     �*  
   �*     �*     �*     +     +     -+     J+     c+     +     �+     �+     �+  &   �+  !   �+     ,     0,     I,     [,     n,  !   �,     �,  A  �,  n  �-  Y  c/  Y  �0  �  2  n  �3  [  5     m6     �6     �6     �6     �6     �6     �6     �6  P   �6  F   7  V   ^7     �7     �7     �7  
   �7     �7     �7     8     8     %8  	   A8  
   K8     V8     p8  P   �8     �8     �8      �8     9  	   #9     -9  ,   F9  5   s9  .   �9     �9     �9  
   �9  %   �9  
   :     ':     0:     ?:  .   D:     s:     y:     �:     �:  	   �:     �:     �:  Y   �:     6;     J;  
   h;  
   s;     ~;     �;     �;     �;  !   �;  B   �;  B   (<  k   k<  ^   �<  ]   6=  &   �=  \   �=  &   >     ?>     \>     c>     f>  /   o>  0   �>  D   �>  Q   ?     g?     u?     �?     �?  %   �?     �?     �?     �?     �?     �?  	   �?     �?     @     %@     ,@     ;@  	   @@     J@     Z@     b@     h@     |@  
   �@  	   �@     �@     �@  Y   �@  "   A     ;A  
   ZA  �  eA  y   'C     �C     �C  	   �C     �C     �C  >   �C  	   D  	   D     'D     8D     JD     RD     [D     cD     gD  
   lD     wD     D     �D     �D  ]   �D     E     E     5E     PE  	   hE     rE  m   �E  �   �E     sF  .   �F     �F  d   �F     2G     AG  (   ^G     �G     �G     �G     �G     �G     �G     �G     �G     �G     �G     H     H     H  !   ,H     NH     gH     vH     �H     �H     �H     �H     �H  
   �H  
   �H     �H     I     I  &   3I  %   ZI     �I     �I     �I     �I     �I  +   �I     J  "   J     @J     OJ     dJ     �J     �J     �J     �J     �J     �J     K     K     6K     MK     f      
      �       z       �   �       C   �   9       �       �   ^   L   a   �   2   %       q   c   g              �   �   �   t           '   �   �      s                 �   )   �   �   ]   J   Z            �   x   ~       �   �   �      1       w   v   O   !   G   �   -   �           R   �   �   �      �   �   �       @          �       4   �   M       �   T                     �   5       �   Q   �   �      [       H   :   `   ?   P   #       D   �   E   �   d   �   ;   �   �      o   >   /       �   �                  {   �   m          �   u       �   �              �               �          X   N   k   e   Y   W           �   8              U       \   0       �   �   �                     �   |   �       �   �       }   �   r       A   �   j   6   y         �   �   �   �       <       �   *   S   "   n      .       b       �   �       h   =   3       (       �   i   B   ,   �           +              �   I               l   �   &   K   V      p   	   F       7   _   �       �       �          �   �   �       $    
            
            <p>
            Hello,<br/><br/>

            ${ctx.get('manager_name')} has approved Quotation <a href="${object.base_url}">${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name})</a><br/>
            </p>
            best regards,<br/>
               O2 network team
            
             
            
            <p>
            Hello,<br/><br/>

            Quotation <a href="${object.base_url}">${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name})</a> has been canceled.<br/>
            </p>
            best regards,<br/>
               O2 network team
            
             
            
            <p>
            Hello,<br/><br/>

            Quotation <a href="${object.base_url}">${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name})</a> is approved.<br/>
            </p>
            best regards,<br/>
               O2 network team
            
             
            
            <p>
            Hello,<br/><br/>

            Vendor "${object.vendor_id.display_name}" has unfinished Quotation <a href="${object.base_url}">${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name})</a><br/>
            </p>
            best regards,<br/>
               O2 network team
            
             
            
            <p>
            Hello,<br/><br/>

            Warning awaiting approval for Quotation <a href="${object.base_url}">${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name})</a><br/>
            </p>
            best regards,<br/>
               O2 network team
            
             
            
            <p>
            Hello,<br/><br/>

            You've been assigned to Quotation <a href="${object.base_url}">${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name})</a><br/>
            </p>
            best regards,<br/>
               O2 network team
            
             <strong>End date:</strong> <strong>Financial code:</strong> <strong>PC:</strong> <strong>PM:</strong> <strong>Project number:</strong> <strong>Short name:</strong> <strong>Start date:</strong> <strong>Vendor:</strong> <ul class =o_mail_thread_message_tracking><li>Workflow reason: %s </li></ul> <ul class=o_mail_thread_message_tracking><li>: %s approved.</li></ul> <ul class=o_mail_thread_message_tracking><li>: %s archived quotation.</li></ul> Action Needed Active Administrator Approve Approved Approved Quotations Archive Archived Archived Quotations Assign Assigned Assigned Quotations Assigned persons Attention, quotation for this financial code has already been approved ! Atypical items Builders pricelist Can user execute workflow action Cancel Canceled Canceled Quotations Click for establishment of new section. Click here for establishment of new Quotation header. Click to create a new package. Code Code item Confirm Confirm quotation approval Created by Created on Cubic meter Currency Date of the last message posted on the record. Description Display Name Draft Duplicate quotations Duplicities Email for SAP export End date Enter workflow reason mainly for actions "Return for repair" and "Cancel" Export file Export file name Export for SAP Export to SAP Financial code Followers Followers (Channels) Followers (Partners) Here is the list of price lists's packages. Here you can find Quotations assigned to vendor. Here you can find Quotations in progress, where you are the vendor. Here you can find Quotations waiting for approval, which are assigned to you or you are thier vendor. Here you can find all Quotations, which are assigned to you or you are their vendor. Here you can find approved Quotations, which are assigned to you or you are thier vendor. Here you can find archived Quotations. Here you can find canceled Quotations, which are assigned to you or you are thier vendor. Here you can find founded Quotations. Here you can find list of section. Hour ID ITEMS If checked new messages require your attention. If checked, new messages require your attention. If quotation is approved, email with SAP export file will be send In case the price limit is exceeded, Quotation must be approved by a given person In progress Internal ID Internal code Is Follower Is current user assigned Item Items Items total: KSZ Kilogram Kilometer Last Message Date Last Modified on Last Updated by Last Updated on Link Manager Measure unit Messages Meter My Quotations Name Not given Note Notification interval Number of Actions Number of days, after which the notification will be send (email) Number of messages which requires an action Number of unread messages O2 Network O2 Slovakia, s.r.o. | Einsteinova 24 | 851 01 Bratislava | Slovakia<br/>
                        E-mail: info@o2.sk | Website: http://www.o2.sk | IČO: 35848863 | DIČ: 2020216748 | IČ DPH: SK2020216748<br/>
                        Zapísaná v OR SR: OS Bratislava I, odd: Sro, vložka číslo: 27882/B<br/>
                        Bankové spojenie: UniCredit Bank Czech Republic and Slovakia, a.s.: IBAN SK4211110000001156173009 - SWIFT UNCRSKBX Only quotation in state 'DRAFT' can be unlink. In any other case use workflow action 'CANCEL' Overview Overview Quotations PACKAGES PC PM PO_${object.name}/${object.shortname}/${object.financial_code} Package Packages Packages total Packages total: Partner Partners Person Piece Price Price limit Price list Price list code Price list item Price list items Price list with the same name already exists. Please choose an unique name. Pricelist Project coordinator (PC) Project manager (PM) Project number (PSID) Quantity Quotation Quotation ${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name}) Quotation ${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name}) is awaiting approval Quotation (PDF) Quotation does not have vendor assigned Quotation draft Quotation with the same name already exists. Please enter an unique name. Quotations Quotations in progres Quotations waiting for approval RO date From To Return to correct Section Send to approve Set Short name Square meter Standard meter Start date State To approve To progress Total price Total price - atypical items Total price - items Total price: Unit of measure Unit price Unite price Unread Messages Unread Messages Counter VL Valid from Valid to Vendor Vendor's pricelist Workflow reason You do not have permission for workflow action current assigned group date state o2net - item o2net - price list o2net - price list item o2net - price offer o2net - price offer atypical o2net - price offer item o2net - price offer package o2net - section o2net.confirm_wizard o2net.quotation.config.settings o2net.wf_confirm vystavba - atyp polozka cenovej ponuky vystavba - balicek cenovej ponuky vystavba - cennik vystavba - cenova ponuka vystavba - oddiel vystavba - polozka vystavba - polozka cennika vystavba - polozka cenovej ponuky wizard Project-Id-Version: Odoo Server 9.0c
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2017-08-23 21:20+0000
PO-Revision-Date: 2017-08-23 23:23+0200
Last-Translator: <>
Language-Team: 
Language: sk
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: 
X-Generator: Poedit 2.0.3
 
            
            <p>
            Dobrý deň,<br/><br/>

            ${ctx.get('manager_name')} schváliL cenovú ponuku <a href="${object.base_url}">${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name})</a><br/>
            </p>
            s pozdravom,<br/>
               O2 network team
            
             
            
            <p>
            Dobrý deň,<br/><br/>

            Cenová ponuka <a href="${object.base_url}">${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name})</a> bola zrušená.<br/>
            </p>
            s pozdravom,<br/>
               O2 network team
            
             
            
            <p>
            Dobrý deň,<br/><br/>

            Cenová ponuka <a href="${object.base_url}">${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name})</a> je schválená.<br/>
            </p>
            s pozdravom,<br/>
               O2 network team
            
             
            
            <p>
            Dobrý deň,<br/><br/>

            Dodávateľ "${object.vendor_id.display_name}" má rozpracovanú cenovú ponuku <a href="${object.base_url}">${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name})</a><br/>
            </p>
            s pozdravom,<br/>
               O2 network team
            
             
            
            <p>
            Dobrý deň,<br/><br/>

            Upozornenie! Cenová ponuka <a href="${object.base_url}">${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name})</a><br/> očakáva schválenie. 
            </p>
            s pozdravom,<br/>
               O2 network team
            
             
            
            <p>
            Dobrý deň,<br/><br/>

            Máte príradenú cenová ponuku <a href="${object.base_url}">${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name})</a><br/>
            </p>
            s pozdravom,<br/>
               O2 network team
            
             Dátum ukončenia: Finančný kód: PC: PM: PSID: Skratka: Dátum začatia: Dodávateľ: <ul class =o_mail_thread_message_tracking><li>Dôvod pre wrokflow: %s </li></ul> <ul class=o_mail_thread_message_tracking><li>: %s schválil.</li></ul> <ul class=o_mail_thread_message_tracking><li>: %s archivoval cenovú ponuku.</li></ul> Potrebná akcia Aktívne Administrátor Schváliť Schválené Schválené cenové ponuky Archivuj Archivované Archivované cenové ponuky Priradiť Priradené Priradené cenové ponuky Priradená osoba Pozor, v minulosti sa už schvaľovala cenova ponuka pre tento finančný kód ! Atypové položky Výstavbový cenník Can user execute workflow action Zrušiť Zrušené Zrušené cenové ponuky Sem kliknite pre založenie nového oddielu. Sem kliknite pre založenie hlavičky cenovej ponuky. Sem kliknite pre založenie nového balíčka. Kód Kód položky Potvrdenie Potvrdenie schválenia cenovej ponuky Vytvorené Vytvoril Kubický meter Mena Date of the last message posted on the record. Popis Názov zobrazenia Návrh Duplicitné cenové ponuky Duplicity eMail - SAP export Dátum ukončenia Uveďte dôvod pre zmenu stavu workflow, najme pre akciu "Vratiť na opravu" a "Zrušiť" Exportovaný súbor Názov exportovaného súboru Export SAP Export SAP Finančný kód Pozorovatelia Pozorovatelia Pozorovatelia (Partnery) Zoznam balíčkov cenovej ponuky. Tu nájdete cenové ponuky, ktoré sú priradené na dodávateľa. Tu nájdete rozpracované cenové ponuky, kde ste ich dodávateľ. Tu nájdete cenové ponuky čakajúce na schválenie, ktoré sú vám priradené alebo ste ich dodávateľ. Tu nájdete schválené cenové ponuky, ktoré vám boli priradené alebo ste ich dodávateľ. Tu nájdete schválené cenové ponuky, ktoré sú vám priradené alebo ste ich dodávateľ. Tu nájdete založené cenové ponuky. Tu nájdete zrušené cenové ponuky, ktoré vám boli priradené alebo ste ich dodávateľ. Tu nájdete založené cenové ponuky. Tu nájdete zoznam oddielov. Hodina ID POLOŽKY If checked new messages require your attention. If checked, new messages require your attention. Ak je schválená cenová ponuka, zašle sa mail so súborom pre SAP In case the price limit is exceeded, Quotation must be approved by a given person Rozpracované Interné ID Interný kód Je pozorovateľ Je aktuálny užívateľ prihlásený Položka Položky Položky celkom: KSZ Kilogram Kilometer Dátum poslednej správy Dátum zmeny Zmenil Dátum zápisu Link Manažér Merná jednotka Správa Meter Moje cenové ponuky Meno Neurčený Poznámka Interval pre notifikáciu Číslo akcie Po koľkých dňoch od poslednej pripomienky sa má opatovne poslať notifikácia (email) Počet správ vyžadujúcich akciu Počet neprečítaných správ O2 Network O2 Slovakia, s.r.o. | Einsteinova 24 | 851 01 Bratislava | Slovakia<br/>
                        E-mail: info@o2.sk | Website: http://www.o2.sk | IČO: 35848863 | DIČ: 2020216748 | IČ DPH: SK2020216748<br/>
                        Zapísaná v OR SR: OS Bratislava I, odd: Sro, vložka číslo: 27882/B<br/>
                        Bankové spojenie: UniCredit Bank Czech Republic and Slovakia, a.s.: IBAN SK4211110000001156173009 - SWIFT UNCRSKBX Cenovú ponuku je možné zmazať len pokiaľ je v stave 'Návrh'. V ostatnom prípade použite workflow akciu 'Zrušiť' Prehľad Prehľad cenových ponúk BALÍČKY PC PM CP_${object.name}/${object.shortname}/${object.financial_code} Balíček Balíčky Balíčky celkom Balíčky celkom: Partner Partneri Partner Kus Cena Limit ceny Cenník Kód cenníka Položka cenníka Položky cenníka Cenník s rovnakým názvom už existuje. Prosím zvoľte iný názov, ktorý bude unikátny. Cenník Projektový koordinátor (PC) Projektový manažér (PM) Číslo projektu (PSID) Množstvo Cenová ponuka Cenová ponuka ${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name}) Cenová ponuka ${object.name}/${object.shortname}/${object.financial_code} (${object.vendor_id.display_name}) očakáva schválenie Cenová ponuka (PDF) Cenová ponuka nemá priradeného dodávateľa Návrh cenovej ponuky Cenová ponuka s rovnakým názvom už existuje. Prosím zvoľte iný názov, ktorý bude unikátny. Cenové ponuky Rozpracované cenové ponuky Cenové ponuky čakajúce na schválenie RO date From To Späť na opravu Oddiel Odoslať na schválenie Sada Skratka Štvorcový meter Meter Dátum začiatku Stav Na schválenie Rozpracovať Celková cena Celková cena - atypové položky Celková cena - položky Celková cena: Merná jednotka Jednotková cena Jednotková cena Neprečítané správy Počet neprečítaných správ VL Platný od Platný do Dodávateľ Cenové ponuky dodávateľa Dôvod pre workflow Nemáte právo na túto workflow akciu je aktuálny užívateľ prihlásený Dátum stavu o2net - Produkt o2net - Cenník o2net - Položka cenníka o2net - Cenník o2net - Cenová ponuka - Atypická položka o2net - Položka cenníka o2net - Cenová ponuka - Balíček o2net - Oddiel o2net.confirm_wizard o2net.quotation.config.settings o2net.wf_confirm sub page Cenova ponuka sub page Cenova ponuka sub page Cenova ponuka sub page Cenova ponuka sub page Cenova ponuka sub page Cenova ponuka sub page Cenova ponuka sub page Cenova ponuka wizard 