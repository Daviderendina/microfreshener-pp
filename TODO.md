## Generale
-  Pensare alla validazione
-  Gennaio presentazione: demo + slide

## Develop
- Il parametro output che viene passato al main non viene utilizzato
- microFreshener-core get_node_by_name
-  Modificate la definizione di **microTOSCA**
-  Fare il push del _core_ (lo modifiche sono sull'altro branch)
- Fare i vari TODO
- [Matebook] Estendere microFreshener per garantire compatiblità con i nuovi nodi


- ~~[Matebook] NodePort gestisce solamente il range  30000 to 32767~~
- ~~Usare ignore node nella demo~~
- ~~Ripristinare i nomi dei nodi originali dopo che il worker li modifica~~
- ~~In split services piuttosto che usare _1, _2, etc.. posso più elegantemente usare il nome del container per differenziarli!!~~
- ~~ComputeNode non viene esportato (e importato!), bisogna cambiare le classi di microfreshener-core !!!~~
- ~~Attenzione: name.ns.svc.cluster.local ma la parte in grassetto ME LA SONO INVENTATA IO!! C'È SOLO SVC PER APPUNTO I SERVICE.~~
- ~~In MicroToscaModel.get_node_by_name devo fare che se passo un type None, prende in automatico tutti i nodi! Poi vedo di sistemare il next(iter(..)) mancante~~
- ~~Attenzione alla _get_obj_by_name_~~
- ~~Fare il report del refactoring~~
- ~~Il nome da solo non identifica, serve anche il tipo!! Per ora c'è il metodo _get_node_by_name_ con il tipo, però forse è meglio avere il tipo direttamente nel nome (tipo nei vari controlli senza passare da quel metodo il tipo non viene checked!! e so per certo in alcuni casi di aver preso il primo disponibile)~~
- ~~Uso i cotruttori per inizializzare Worker: NO! Non hanno stato, sono solo esecutori one-shot~~
- ~~Tutti i worker devono avere la dipendenza dal name~~
- ~~Fare refactoring totale dei Refactoring (csì da sistemare anche tutte le questioni di nomi, metodi, etc..)~~

## Testing
-  Testare il solver
- Testare YMLImporter con i nuovi nodi
- Testare anche con JSON i modelli?


-  ~~Controllare che tutto viene effettuato nel modo giusto, aiutandosi col report~~
-  ~~Testare il core con le nuove modifiche~~
- ~~Testare lo sniffer nuovo~~

## Aggiunte successive
- Migliorare l'ignorer: lo importo, e poi in ogni classe (solver, etc..) setto cosa c'è da ignorare: in questo modo, tolgo la dipendenza diretta tra Ignorer e Worker
-  Penso che se viene dato il nome in automatico ad es. usando generate name, si spacchi tutto!
- Se tutto quello definito con istio non ha il ns, devo aggiungere al nome il ns dell'oggetto che lo definisce
- Compatibilità con microMiner
- Fare un worker che mi controlla tutti i Service e me li converte in Container, sia per quando riguarda il nome che (soprattutto) per quanto riguarda i container multipli. Se c'è un Service che è in realtà un Pod che definisce due container, genero i nodi necessari

#### Garantire compatibilità con microMiner
microTOSCA genera:
- un nodo Service con nome NAME.SERVICE per tutti i Pod e PodDefiner
- mette .svc per ogni nodo di tipo svc
- Gli ingress non si capisce bene come li gestisce: di certo non chiama con nome.ns dell'Ingress, quindi è un poò difficile fare il match. Inoltre mette un ingress-controller per tutti mi sa, da approfondire meglio

Per garantire questa compatibilità dovrei discuterne con Jacopo. Il problema degli Ingress non è banale!! L'unica cosa che mi viene in mente è togliere dal modello tutti i nodi che non finiscono con **.svc** (sono per forza ingress) e farli rimettere tutti dal mio worker

Comunque l'idea iniziale era fare un worker che mi sistemasse tutto.

Altro problema: il microMiner mi genera un nodo per POD (assunzione), da me è diversa l'assunzione: posso cancellare il nuovo nodo e aggiungere quelli giusti per il mio tool, ma come faccio per le relazioni?
