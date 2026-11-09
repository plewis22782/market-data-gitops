{{- define "fe.name" -}}{{ .Chart.Name }}{{- end -}}
{{- define "fe.labels" -}}
app.kubernetes.io/name: {{ include "fe.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.image.tag | default .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}
{{- define "fe.selector" -}}
app.kubernetes.io/name: {{ include "fe.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
