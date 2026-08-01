package tray

import (
	"github.com/energye/systray/v2"
)

type Actions struct {
	OnOpen    func()
	OnQuit    func()
	OnAbout   func()
	OnDataDir func()
	OnExports func()
	OnLogs    func()
	OnToggleAutostart func()
	AutostartLabel func(enabled bool) string
}

func Run(icon []byte, tooltip string, actions Actions) {
	systray.Run(func() {
		if len(icon) > 0 {
			systray.SetIcon(icon)
		}
		systray.SetTitle("TCG Tools")
		systray.SetTooltip(tooltip)

		mOpen := systray.AddMenuItem("Abrir TCG Tools", "")
		mAbout := systray.AddMenuItem("Sobre / versao", "")
		systray.AddSeparator()
		mData := systray.AddMenuItem("Abrir pasta de dados", "")
		mExports := systray.AddMenuItem("Abrir pasta exports", "")
		mLogs := systray.AddMenuItem("Abrir pasta logs", "")
		autoLabel := "Iniciar com Windows"
		if actions.AutostartLabel != nil {
			autoLabel = actions.AutostartLabel(false)
		}
		mAuto := systray.AddMenuItem(autoLabel, "")
		systray.AddSeparator()
		mQuit := systray.AddMenuItem("Encerrar", "")

		go func() {
			for {
				select {
				case <-mOpen.ClickedCh:
					if actions.OnOpen != nil {
						actions.OnOpen()
					}
				case <-mAbout.ClickedCh:
					if actions.OnAbout != nil {
						actions.OnAbout()
					}
				case <-mData.ClickedCh:
					if actions.OnDataDir != nil {
						actions.OnDataDir()
					}
				case <-mExports.ClickedCh:
					if actions.OnExports != nil {
						actions.OnExports()
					}
				case <-mLogs.ClickedCh:
					if actions.OnLogs != nil {
						actions.OnLogs()
					}
				case <-mAuto.ClickedCh:
					if actions.OnToggleAutostart != nil {
						actions.OnToggleAutostart()
					}
					if actions.AutostartLabel != nil {
						enabled := actions.AutostartLabel(false)
						if enabled == "Desativar inicio com Windows" {
							mAuto.SetTitle("Desativar inicio com Windows")
						} else {
							mAuto.SetTitle("Ativar inicio com Windows")
						}
					}
				case <-mQuit.ClickedCh:
					if actions.OnQuit != nil {
						actions.OnQuit()
					}
					systray.Quit()
					return
				}
			}
		}()
	}, func() {})
}

func Quit() {
	systray.Quit()
}
