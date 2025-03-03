{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}

{{- define "number-verification-backend-app.fullname" -}}
{{- printf "%s" .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Labels.
*/}}

{{- define "number-verification-backend-app.labels" }}
app: {{ .Chart.Name }}
chart: "{{ .Chart.Name }}-{{ .Chart.Version }}"
heritage: {{ .Release.Service }}
release: {{ .Release.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/name: {{ print ( .Values.nameOverride | default .Chart.Name | default .Release.Name ) | trunc 63 | trimSuffix "-" }}
helm.sh/chart: "{{ .Chart.Name }}-{{ .Chart.Version }}"
{{- end }}

{{- define "number-verification-backend-app.matchLabels" }}
app: {{ print ( .Values.nameOverride | default .Chart.Name | default .Release.Name ) | trunc 63 | trimSuffix "-" }}
release: {{ .Release.Name }}
{{- end -}}
