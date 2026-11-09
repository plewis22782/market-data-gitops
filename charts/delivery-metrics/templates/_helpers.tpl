{{- define "dm.name" -}}{{ .Chart.Name }}{{- end -}}
{{- define "dm.labels" -}}
app.kubernetes.io/name: {{ include "dm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.image.tag | default .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}
{{- define "dm.selector" -}}
app.kubernetes.io/name: {{ include "dm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
