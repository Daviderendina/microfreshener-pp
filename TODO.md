### Generale
- [ ] Modificate la definizione di **microTOSCA**
- [ ] Fare il push del _core_
- [ ] Pensare alla validazione
- [ ] Gennaio presentazione: demo + slide
- [ ] Il nome da solo non identifica, serve anche il tipo!! Per ora c'è il metodo _get_node_by_name_ con il tipo, però forse è meglio avere il tipo direttamente nel nome (tipo nei vari controlli senza passare da quel metodo il tipo non viene checked!! e so per certo in alcuni casi di aver preso il primo disponibile)
- [ ] Fare il report del refactoring
- [ ] Attenzione: name.ns.svc **.cluster.local** ma la parte in grassetto ME LA SONO INVENTATA IO!! C'È SOLO SVC PER APPUNTO I SERVICE.

### microFreshener
- [ ] Estenderlo per garantire la compatibilità con i nuovi nodi

### Testing
- [ ] Testare il solver
- [ ] Testare lo sniffer nuovo
- [ ] Testare il core con le nuove modifiche

### Garantire compatibilità con microTosca
microTOSCA genera:
- un nodo Service con nome NAME.SERVICE per tutti i Pod e PodDefiner
- mette .svc per ogni nodo di tipo svc
- Gli ingress non si capisce bene come li gestisce: di certo non chiama con nome.ns dell'Ingress, quindi è un poò difficile fare il match. Inoltre mette un ingress-controller per tutti mi sa, da approfondire meglio

Per garantire questa compatibilità dovrei discuterne con Jacopo. Il problema degli Ingress non è banale!! L'unica cosa che mi viene in mente è togliere dal modello tutti i nodi che non finiscono con **.svc** (sono per forza ingress) e farli rimettere tutti dal mio worker

Comunque l'idea iniziale era fare un worker che mi sistemasse tutto.

Altro problema: il microMiner mi genera un nodo per POD (assunzione), da me è diversa l'assunzione: posso cancellare il nuovo nodo e aggiungere quelli giusti per il mio tool, ma come faccio per le relazioni?
