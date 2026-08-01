package tray

func AutostartMenuTitle(enabled bool) string {
	if enabled {
		return "Desativar inicio com Windows"
	}
	return "Ativar inicio com Windows"
}
