from pulp import LpMinimize, LpProblem, LpVariable
import random
import copy
import sys

class Tournoi:
    def __init__(self, nbEquipe):

        self.nbEquipe = nbEquipe
        self.nbSemaine = nbEquipe - 1
        self.nbPeriode = nbEquipe // 2
        self.tableau = [[(None,None) for i in range(self.nbPeriode)] for j in range(self.nbSemaine)]
        self.match_en_erreur = []
        self.match_bon = []

    def __str__(self):
        tournoi = "\n"
        nbSem = 0
        for semaine in self.tableau:
            tournoi += "Semaine " + str(nbSem) + ": \n"
            nbPer = 0
            matcheSem = ""
            for match in semaine:
                e0 = " "
                e1 = " "
                if match[0] != None:
                    e0 = str(match[0])
                    e1 = str(match[1])
                matcheSem += "P" + str(nbPer) + " (" + e0 + " vs " + e1 + ") | "
                nbPer += 1
            tournoi += matcheSem + "\n"
            nbSem += 1
        return tournoi

    def solve(self,sDebut,sFin):
        # Liste de match a placer
        combinaisons= [(i, j) for i in range(self.nbEquipe) for j in range(self.nbEquipe) if i<j]

        problem = LpProblem(name="Planification de rencontres sportives", sense=LpMinimize)

        ####### Variables #######
        match_vars = {(i, j, s, p): LpVariable(name=f"match_{i}_{j}_{s}_{p}", cat="Binary")for i, j in combinaisons for s in range(self.nbSemaine) for p in range(self.nbPeriode)}

        ####### Contraintes ######

        # Solution partielle existante (si solve depuis solution partielle)

        for s in range(self.nbSemaine):
            for p in range(self.nbPeriode):
                e1 =self.tableau[s][p][0]
                e2 = self.tableau[s][p][1]
                if e1 != None:
                    problem += match_vars[e1, e2, s, p] == 1

        # Symetrie
        e1=0
        e2=1
        for p in range(self.nbPeriode):
            problem += match_vars[e1, e2, 0, p] ==1
            e1+=2
            e2+=2

        # Exactement une fois par semaine
        for i in range(self.nbEquipe):
            for s in range(sDebut,sFin):
                problem += sum(match_vars[i, j, s, p] for j in range(self.nbEquipe) if i<j for p in range(self.nbPeriode)) + sum(match_vars[j, i, s, p] for j in range(self.nbEquipe) if i>j for p in range(self.nbPeriode)) == 1, f"UnMatchParSemaine_{i}_{s}"

        # Maximum deux fois par periode
        if self.nbSemaine<=16:
            for i in range(self.nbEquipe):
            # for p in range(self.nbPeriode):
                problem += sum(match_vars[i, j, s, 0] for j in range(self.nbEquipe) if i<j for s in range(self.nbSemaine)) + sum(match_vars[j, i, s, 0] for j in range(self.nbEquipe) if i>j for s in range(self.nbSemaine)) <= 2, f"DeuxMatchParPeriode_{i}_{p}"
            
        # Aucun crenaux doit etre vide
        for s in range(sDebut,sFin):
            for p in range(self.nbPeriode):
                problem += sum(match_vars[i, j, s, p] for i,j in combinaisons) ==1, f"AucunCrenauxVide_{s}_{p}"

        # Chaque equipe joue contre tout le monde exactement une fois
        if(sFin == self.nbSemaine):
            for i,j in combinaisons:
                    problem += sum(match_vars[i, j, s, p] for s in range(sDebut,sFin) for p in range(self.nbPeriode)) ==1, f"ChaqueEquipeVsChaqueEquipe_{i}_{j}"
        else:
            for i,j in combinaisons:
                    problem += sum(match_vars[i, j, s, p] for s in range(sDebut,sFin) for p in range(self.nbPeriode)) <=1, f"ChaqueEquipeVsChaqueEquipe_{i}_{j}"

        problem.solve()

        ####### Complete le tableau avec la solution trouvé (complète ou partiel) #######
        for i, j in combinaisons:
            for s in range(sDebut,sFin):
                for p in range(self.nbPeriode):
                    if match_vars[i, j, s, p].value() == 1:
                        self.tableau[s][p] = (i, j)

        return problem.status == 1 
    
    def generer_solutions_voisines(self,all_match,match_en_erreur_i,match_switch):

        #match:  0: match || 1: semaine || 2: periode || 3: penalite eq1 || 4: penalité eq2
        list_voisins = []
        match1=self.match_en_erreur[match_en_erreur_i]    
        index_match_erreur  = all_match.index(match1) + 1
        m1 = match1[0]
        m1_sem=match1[1]
        m1_per=match1[2]
        for match2 in all_match[index_match_erreur:]:
            m2 = match2[0]
            if([m1,m2] not in match_switch and [m2,m1] not in match_switch and match2[1]==m1_sem and match2 != match1):
                m2_sem=match2[1]
                m2_per=match2[2]
                t2=copy.deepcopy(self)
                a_calculer=[]
                a_calculer.append([m1_per,m2_per])
                ancien_penalite,_=verifMatch(t2,a_calculer=a_calculer)
                # echange des match
                t2.tableau[m1_sem][m1_per]=m2
                t2.tableau[m2_sem][m2_per]=m1
                # calcul nouvelle penalité
                nouvelle_penalite,_=verifMatch(t2,a_calculer=a_calculer)
                list_voisins.append([t2,ancien_penalite,nouvelle_penalite,match1,match2]) 
        list_voisins.sort(key=self.sort_voisin,reverse=True)
        return list_voisins

    def recherche_locale_descente(self):
        # Solution initiale:
        self.solve(0, self.nbSemaine)
        for sem in range(1,self.nbSemaine):
            match_sem = []
            for per in range(1,self.nbPeriode):
                match_sem.append(self.tableau[sem][per])
            random.shuffle(match_sem)
            for i in range(len(match_sem)):
                self.tableau[sem][i+1]=match_sem[i]

        print("Solution initale: ")
        print(self)
        verifTableau(self)
        print("\noptimisation ...\n")
        iter=0
        opti_trouver = False
        match_switch=[]
        best_sol = copy.deepcopy(self.tableau)
        old_optimal = self.nbPeriode*self.nbSemaine
        self.set_type_match()
        current_optimal = len(self.match_en_erreur)
        sans_solution=False
        
        while current_optimal!=0 and iter!=30000 and sans_solution==False:
            opti_trouver = False
            all_match=[]
            all_match=self.match_en_erreur + self.match_bon 
            # recherche de voisin améliorant
            for match_en_erreur_i in range(len(self.match_en_erreur)):
                if opti_trouver == False:    
                    voisin_i = self.generer_solutions_voisines(all_match,match_en_erreur_i,match_switch)
                    for voisin in voisin_i:
                        if opti_trouver == False:
                            ancienne_penalite = voisin[1]
                            nouvelle_penalite = voisin[2]
                            match1 = voisin[3]
                            match2 = voisin[4]
                            if ancienne_penalite>nouvelle_penalite:
                                self.tableau = voisin[0].tableau
                                opti_trouver = True
                                m1 = match1[0]
                                m2 = match2[0]
                                match_switch.append([m1,m2])
                                iter+=1

            # Perturbation si aucun voisin améliorant
            if opti_trouver == False:

                # on prend un match random parmis les match avec la penalite la plus forte dans la periode P ou il y a le plus de match en erreur
                per_max_erreur = self.match_en_erreur[0][2]
                matchs_erreur_per = [match for match in self.match_en_erreur if match[2] == per_max_erreur]
                matchs_erreur_per.sort(key=self.sort_by_pena,reverse=True)
                max_erreur = matchs_erreur_per[0][3] + matchs_erreur_per[0][4]
                match_en_erreur_per_max = [match for match in matchs_erreur_per if match[3]+match[4] == max_erreur]
                match1 = random.choice(match_en_erreur_per_max)
                m1=match1[0]
                sem_match1=match1[1]
                per_match1=match1[2]

                # On prend comme deuxieme matche un match de la meme semaine que le premier. On choisis celui qui aporte une penalite la plus petite apres l echange 
                list_match2 = [ match for match in all_match if match1!=match and match[1] == sem_match1 and [m1,match[0]] not in match_switch and [match[0],m1] not in match_switch]
                best_penalite = None
                list_match2_best = []
                for match in list_match2:
                    sem_match=match[1]
                    per_match=match[2]
                    m=match[0]
                    tournoi_copy = copy.deepcopy(self)
                    tournoi_copy.tableau[sem_match1][per_match1]=m
                    tournoi_copy.tableau[sem_match][per_match]=m1
                    penalite,_ = verifMatch(tournoi_copy,a_calculer=[[per_match1,per_match]])
                    if best_penalite == None or best_penalite > penalite:
                        best_penalite = penalite
                        list_match2_best = []
                        list_match2_best.append(match)
                    elif best_penalite == penalite:
                        list_match2_best.append(match)

                if len(list_match2_best) == 0:
                    print("Pas de solution pour "+str(self.nbEquipe)+" equipes")
                    sans_solution=True
                if sans_solution == False:
                    match2 = random.choice(list_match2_best)

                    # On effectue le changement
                    sem_match2=match2[1]
                    per_match2=match2[2]
                    m2=match2[0]
                    self.tableau[sem_match1][per_match1]=m2
                    self.tableau[sem_match2][per_match2]=m1
                    match_switch = []
                    match_switch.append([m1,m2])
                    iter+=1
                
            self.set_type_match()
            current_optimal = len(self.match_en_erreur)
            
            if current_optimal<old_optimal:
                old_optimal=current_optimal
                best_sol = copy.deepcopy(self.tableau)

        
        print("Nombre d iteration: "+str(iter))
        self.tableau = best_sol

    def set_type_match(self):
        # remplie la liste de match en erreur
        self.match_bon=[]    
        self.match_en_erreur=[]
        for s in range(1,self.nbSemaine):
            for p in range(0,self.nbPeriode): 
                penalite1,penalite2 = verifMatch(self,sem=s,per=p)
                if penalite1+penalite2==0:
                    self.match_bon.append([self.tableau[s][p],s,p,penalite1,penalite2])
                else:
                    self.match_en_erreur.append([self.tableau[s][p],s,p,penalite1,penalite2])
        self.match_en_erreur.sort(key=self.sort_by_per,reverse=True)
    
    def sort_by_per(self,un_match):
        # retourne le nombre de match en erreur dans la periode du match un_match
        list_err_per = self.get_nb_err_periode()
        return list_err_per[un_match[2]]
    
    def get_nb_err_periode(self):
        # retourne le nombre d erreur par periode
        list_err_per = [0 for i in range(self.nbPeriode)]
        for num_per in range(self.nbPeriode):
            nb= 0
            for match in self.match_en_erreur:
                if match[2] == num_per:
                    nb+=1
            list_err_per[num_per]=nb
        return list_err_per
    
    def sort_by_pena(self,un_match):
        # retourne la penalite de l equipe 1 + penalite de l equipe 2 (entre 0 et 2) 
        return un_match[3]+un_match[4]
    
    def sort_voisin(self,un_voisin):
        # retourne la baisse de penalite (ancienne penalite - nouvelle penalite) puis trie dans l ordre decroissant
        # équivaut a retourner un_voisin[2] puis trié dans l ordre croissant.
        return un_voisin[1]-un_voisin[2]

def verifTableau(tournoi,justif = False):

    res = True
    penalite = 0
    combinaisons= [(i, j) for i in range(tournoi.nbEquipe) for j in range(tournoi.nbEquipe) if i<j]
    for match in combinaisons:
        count = 0
        for sem in tournoi.tableau:
            if match in sem:
                count+=1
        if count>1:
            if justif:
                print("erreur: le match ("+str(match[0])+" vs "+str(match[1])+") est joué deux fois")
            res = False
        if count<1:
            if justif:
                print("erreur: le match ("+str(match[0])+" vs "+str(match[1])+") n est pas joué")
            res = False
        
    for equ in range(tournoi.nbEquipe):
        for sem in tournoi.tableau:
            count = 0
            for match in sem:
                if equ == match[0] or equ == match[1]:
                    count+=1
            if count>1:
                penalite+=1
                if justif:
                    print("erreur: l equipe "+str(equ)+ " joue deux fois dans la semaine "+str(tournoi.tableau.index(sem)))
                res =  False
            if count<1:
                penalite+=1
                if justif:
                    print("erreur: l equipe "+str(equ)+ " ne joue pas dans la semaine "+str(tournoi.tableau.index(sem)))
                res =  False
    
    for equ in range(tournoi.nbEquipe):
        for per in range(tournoi.nbPeriode):  
            count = 0
            for sem in tournoi.tableau:    
                match = (sem[per][0],sem[per][1])      
                if equ == sem[per][0] or equ == sem[per][1]:
                    count+=1
            if count>2:
                penalite+=1
                if justif:
                    print("erreur: l equipe "+str(equ)+ "joue plus de deux fois dans la periode "+str(per))
                res =  False
            
    if True:
        print("penalite total: "+str(penalite))
    return penalite

def verifMatch(tournoi,sem=None,per=None,a_calculer=None):
    penalite1 = 0
    penalite2 = 0
    # penalite sur tout le tableau
    if sem==None and a_calculer == None:
        return verifTableau(tournoi)
    
    # penalite causer par un match
    elif sem!=None and a_calculer==None:
        eq1=0
        eq2=0
        match = tournoi.tableau[sem][per]
        for semaine in range(tournoi.nbSemaine):
            if tournoi.tableau[semaine][per][0]==match[0] or tournoi.tableau[semaine][per][1]==match[0]:
                eq1+=1
            if tournoi.tableau[semaine][per][0]==match[1] or tournoi.tableau[semaine][per][1]==match[1]:
                eq2+=1
        if eq1>2:
            penalite1+=1
        if eq2>2:
            penalite2+=1

    # penalite sur des semaine et periode donner
    elif sem==None and a_calculer!=None:
        for equ in range(tournoi.nbEquipe):
            for periode in a_calculer[0]:
                apparition_equ=0
                for semaine in range(tournoi.nbSemaine):
                    if equ == tournoi.tableau[semaine][periode][0] or equ == tournoi.tableau[semaine][periode][1]:
                        apparition_equ+=1
                if apparition_equ>2:
                    penalite1+=1

    return penalite1,penalite2

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Utilisation: python3 tour7.py <Nombre d equipe>")
    else:
        nbEquipe = int(sys.argv[1])
        if nbEquipe%2!=0:
            print("Utilisation: le nombre d'équipe doit etre paire")
        else:
            tournoi = Tournoi(nbEquipe)  
            tournoi.recherche_locale_descente()
            print("Solution finale")
            print(tournoi)
            verifTableau(tournoi,True)