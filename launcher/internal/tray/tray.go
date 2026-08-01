package tray

import (
	"github.com/energye/systray"
)

type Actions struct {
	OnOpen            func()
	OnQuit            func()
	OnAbout           func()
	OnDataDir         func()
	OnExports         func()
	OnLogs            func()
	OnToggleAutostart func()
	AutostartEnabled  func() bool
}

func Run(icon []byte, tooltip string, actions Actions) {
	systray.Run(func() {
		if len(icon) > 0 {
			systray.SetIcon(icon)
		}
		systray.SetTitle("TCG Tools")
		systray.SetTooltip(tooltip)

		systray.AddMenuItem("Abrir TCG Tools", "").Click(func() {
			if actions.OnOpen != nil {
				actions.OnOpen()
			}
		})
		systray.AddMenuItem("Sobre / versao", "").Click(func() {
			if actions.OnAbout != nil {
				actions.OnAbout()
			}
		})
		systray.AddSeparator()
		systray.AddMenuItem("Abrir pasta de dados", "").Click(func() {
			if actions.OnDataDir != nil {
				actions.OnDataDir()
			}
		})
		systray.AddMenuItem("Abrir pasta exports", "").Click(func() {
			if actions.OnExports != nil {
				actions.OnExports()
			}
		})
		systray.AddMenuItem("Abrir pasta logs", "").Click(func() {
			if actions.OnLogs != nil {
				actions.OnLogs()
			}
		})

		autoLabel := AutostartMenuTitle(false)
		if actions.AutostartEnabled != nil {
			autoLabel = AutostartMenuTitle(actions.AutostartEnabled())
		}
		mAuto := systray.AddMenuItem(autoLabel, "")
		mAuto.Click(func() {
			if actions.OnToggleAutostart != nil {
				actions.OnToggleAutostart()
			}
			if actions.AutostartEnabled != nil {
				mAuto.SetTitle(AutostartMenuTitle(actions.AutostartEnabled()))
			}
		})

		systray.AddSeparator()
		systray.AddMenuItem("Encerrar", "").Click(func() {
			if actions.OnQuit != nil {
				actions.OnQuit()
			}
			systray.Quit()
		})
	}, func() {})
}

func Quit() {
	systray.Quit()
}
