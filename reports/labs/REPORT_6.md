# Звіт по лабораторній роботі 6

## Посилання на репозиторій

**Repository:** https://github.com/sviathumeniuk/open-data-ai-analytics

## Мета роботи

Впровадити підхід **GitOps** для розгортання аналітичного вебзастосунку в Kubernetes, забезпечивши:

- декларативне описання інфраструктури та застосунку у Git;
- автоматичну синхронізацію стану кластера з репозиторієм;
- можливість відновлення та самовиліковування (self-heal) при дрейфі конфігурації.

## Теоретичні відомості

**GitOps** — це операційна модель, де Git-репозиторій є єдиним джерелом правди (single source of truth) для стану інфраструктури та застосунків. Будь-яка зміна робиться через коміт/PR у Git, а агент у кластері підтягує ці зміни та застосовує їх.

Ключові принципи GitOps:

- **Декларативність:** бажаний стан описаний у YAML/Helm/Kustomize.
- **Версіонування та аудит:** кожна зміна має історію (git log).
- **Автоматичне узгодження:** контролер приводить фактичний стан до бажаного.
- **Rollback:** повернення до попереднього коміту = повернення стану.

**Argo CD** — Kubernetes-оператор/контролер, який реалізує GitOps для застосунків: відстежує репозиторій, порівнює desired state (Git) та live state (кластер) і синхронізує їх.

## Реалізація GitOps у проєкті

Для GitOps створено каталог `gitops/` з двома частинами:

1. `gitops/app/` — Kubernetes-маніфести застосунку.
2. `gitops/argocd/` — опис Argo CD Application, який вказує, що саме потрібно деплоїти з Git.

### Kubernetes-маніфести застосунку

**1) Namespace**

Створено окремий namespace `analytics` для ізоляції ресурсів:

```yaml
apiVersion: v1
kind: Namespace
metadata:
	name: analytics
```

**2) PersistentVolumeClaim (PVC)**

Оскільки застосунок використовує SQLite, потрібне персистентне сховище для файлу БД (`analytics.db`). Для цього додано PVC `analytics-data-pvc` на 1Gi:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
	name: analytics-data-pvc
	namespace: analytics
spec:
	accessModes:
		- ReadWriteOnce
	resources:
		requests:
			storage: 1Gi
```

**3) Deployment з initContainer**

Розгортання побудовано так, щоб **спочатку виконати batch-етап пайплайну**, а вже потім запускати веб.

- `initContainer` `pipeline` запускає `python pipeline/run_all.py` і генерує дані/результати.
- Основний контейнер `web` запускає Flask/Gunicorn і читає SQLite БД з того ж PVC.

Ключові фрагменти (повний маніфест — у `gitops/app/deployment.yaml`):

```yaml
initContainers:
	- name: pipeline
		image: ghcr.io/sviathumeniuk/open-data-ai-analytics:sha-placeholder
		command: ["python", "pipeline/run_all.py"]
		env:
			- name: SQLITE_DB_PATH
				value: "/workspace/data/analytics.db"
			- name: CSV_PATH
				value: "/workspace/raw/pdv_actual_28-08-2019.csv"
		volumeMounts:
			- name: storage
				mountPath: /workspace/data

containers:
	- name: web
		image: ghcr.io/sviathumeniuk/open-data-ai-analytics:sha-placeholder
		ports:
			- containerPort: 8000
		env:
			- name: SQLITE_DB_PATH
				value: "/workspace/data/analytics.db"
		volumeMounts:
			- name: storage
				mountPath: /workspace/data
```

Технічний сенс `initContainer`: він гарантує, що веб-под стартує лише після успішного завершення побудови даних (аналогічно до `depends_on`/batch-етапів у Docker Compose з попередніх лабораторних).

Примітка: у маніфесті використаний тег `sha-placeholder` — його потрібно замінювати на реальний тег образу (наприклад, commit SHA) під час публікації в registry.

**4) Service (NodePort)**

Для доступу ззовні створено `Service` типу NodePort, який проброшуює вебпорт 8000 на порт ноди 30800:

```yaml
apiVersion: v1
kind: Service
metadata:
	name: analytics-service
	namespace: analytics
spec:
	type: NodePort
	selector:
		app: analytics
	ports:
		- protocol: TCP
			port: 80
			targetPort: 8000
			nodePort: 30800
```

### Argo CD Application

У `gitops/argocd/application.yaml` описано Argo CD Application, який вказує:

- який репозиторій брати (`repoURL`),
- який шлях у репозиторії містить маніфести (`path: gitops/app`),
- куди застосовувати (`namespace: analytics`),
- політики автосинху.

Фрагмент конфігурації:

```yaml
spec:
	source:
		repoURL: 'https://github.com/sviathumeniuk/open-data-ai-analytics.git'
		targetRevision: HEAD
		path: gitops/app
	destination:
		server: 'https://kubernetes.default.svc'
		namespace: analytics
	syncPolicy:
		automated:
			prune: true
			selfHeal: true
		syncOptions:
			- CreateNamespace=true
```

Це дає:

- **automated sync** — застосування змін без ручного натискання Sync;
- **prune** — видалення ресурсів, які прибрали з Git;
- **selfHeal** — відновлення стану, якщо хтось змінив ресурс вручну в кластері;
- **CreateNamespace=true** — створення `analytics` namespace автоматично.

## Хід виконання роботи (деплой)

Передумови:

- є Kubernetes-кластер (наприклад, minikube/kind або керований кластер);
- Argo CD встановлено в namespace `argocd`;
- контейнерний образ застосунку опубліковано в registry (у маніфестах — `ghcr.io/...`).

Далі послідовність дій:

1. Додати Application у кластер:

```bash
kubectl apply -n argocd -f gitops/argocd/application.yaml
```

2. Дочекатися, поки Argo CD синхронізує застосунок і створить ресурси в `analytics`:

```bash
kubectl get pods -n analytics
kubectl get svc -n analytics
```

3. Перевірити, що `initContainer` відпрацював успішно (лог пайплайну):

```bash
kubectl logs -n analytics deploy/analytics-web -c pipeline
```

4. Відкрити застосунок:

- через NodePort: `http://79.76.32.243:30800/`

```bash
kubectl port-forward -n analytics svc/analytics-service 8000:80
```

## Результати та перевірка працездатності

Ознаки коректного розгортання:

- у namespace `analytics` є под(и) `analytics-web` зі статусом `Running`;
- у логах `pipeline` є повідомлення `--- Pipeline Finished ---`;
- вебсторінка відображає дашборд і дані з SQLite БД (що означає, що PVC змонтовано та файл БД створено/заповнено).

## Підсумок

У лабораторній роботі 6 реалізовано GitOps-розгортання на базі Argo CD:

- описано бажаний стан застосунку декларативними Kubernetes-маніфестами;
- налаштовано Argo CD Application з automated sync, prune та self-heal;
- забезпечено коректний порядок виконання: спочатку пайплайн (initContainer), потім веб;
- додано персистентність для SQLite через PVC.

