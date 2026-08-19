#pragma once

#include <LovyanGFX.hpp>


class LGFX : public lgfx::LGFX_Device
{

  lgfx::Panel_ILI9488 _panel;
  lgfx::Bus_SPI _bus;
  lgfx::Touch_XPT2046 _touch;


public:


LGFX(void)
{

  // SPI
  {
    auto cfg = _bus.config();

    cfg.spi_host = SPI2_HOST;
    cfg.spi_mode = 0;

    cfg.freq_write = 40000000;
    cfg.freq_read  = 16000000;


    cfg.pin_sclk = 12;
    cfg.pin_mosi = 11;
    cfg.pin_miso = 13;

    cfg.pin_dc = 9;


    _bus.config(cfg);

    _panel.setBus(&_bus);
  }



  // LCD
  {
    auto cfg = _panel.config();


    cfg.pin_cs = 10;
    cfg.pin_rst = 14;


    cfg.panel_width  = 320;
    cfg.panel_height = 480;


    cfg.memory_width  = 320;
    cfg.memory_height = 480;


    cfg.offset_rotation = 0;


    _panel.config(cfg);
  }



  // TOUCH XPT2046
  {
    auto cfg = _touch.config();


    cfg.x_min = 200;
    cfg.x_max = 3800;

    cfg.y_min = 200;
    cfg.y_max = 3800;


    cfg.pin_cs = 21;


    cfg.spi_host = SPI2_HOST;


    cfg.freq = 2500000;


    cfg.pin_sclk = 12;
    cfg.pin_mosi = 11;
    cfg.pin_miso = 13;


    _touch.config(cfg);


    _panel.setTouch(&_touch);
  }



  setPanel(&_panel);

}


};