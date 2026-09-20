# Biovarase — How it works

The program followed while it runs: the start, a login, a chart, a result
entered, an error. Method by method, so that a reader can put a breakpoint
anywhere in this page and find themselves in the code.

## The start

`biovarase.py` holds `main()` and nothing else. It reads the options — there
is one, `--trace` — opens the log first, so that even a failure to start is
written down, and builds the application.

```
main()                          biovarase.py
  Log(...)                      log.py
  App("Biovarase", log)         ui/app.py
```

`App` is the root window. It builds the engine, which builds everything else:

```
App.__init__
  Engine(log)                   engine.py
    Config(biovarase.ini)       config.py      the settings, read line by line
    DBMS(sql/biovarase.sl3)     dbms.py        the connection, foreign keys on
    Tools()                     tools.py       the ttk styles
    QC(config)                  qc.py
    Westgards()                 westgards.py
    Exporter(engine)            exporter.py
    Report(engine)              report.py
    Events(log)                 events.py
    Windows(log)                windows.py
  tools.set_style("clam")
  set_icon()                    the base64 PNGs in the file `icon`
  Login(self).on_open()         ui/login.py
```

Nothing has been read from the database yet. The login is the first window,
and it is a `ttk.Frame` inside the root rather than a Toplevel: the root is
the program, and what fills it changes.

## A login

`Login.on_login` asks the engine, which asks bcrypt:

```
Login.on_login
  engine.on_login(nickname, password)          engine.py
    db.read(False, "SELECT * FROM users ...")
    bcrypt.checkpw(password, row["pswrd"])
  engine.set_log_user(user)
    db.set_session_user(user_id)               the audit triggers read this
  App.show_main()                              ui/app.py
    Main(self).on_open()                       ui/main.py
  self.destroy()
```

Two things happen here that matter later. The session row is written, so
every trigger that fires from now on knows whose work it is recording. And
the login destroys itself: the root window is resized, made resizable, and
filled with `Main`.

## The main window

`Main.on_open` reads the panels and stops. Everything else waits for a
choice:

```
on_open
  set_categories()        the panels that have an analyte in use under them
on_selected_category      → set_tests()          the analytes of that panel
on_selected_test          → set_workstations()   the benches that run it
on_selected_workstation   → set_batches()        the lots open on it
on_selected_batch         → set_results()        and the charts
```

Each step clears what hangs below it. Choosing another analyte empties the
lots, the results, the chart and the statistics, because lots of the analyte
before look exactly like the right ones.

## A chart

`set_results` is where the window fills:

```
set_results
  db.get_selected("batches", "batch_id", batch)          the lot
  db.read(...)                                            the results, by period
  set_charts(lot)
    db.read(...)                                          the last N results
    chart.draw_chart(series, target, sd, dates, status)   ljcanvas.py
    profile.draw_profile(series, target, sd)              profile_canvas.py
  set_statistics(lot)
    engine.get_series(batch, observations)
    qc.get_mean / get_cv / get_bias / get_te / get_uncertainty
    westgards.get_westgard_violation_rule(target, sd, series)
    set_westgard_alarm(rule)                              green or red
```

Two limits are at work and they answer different questions. The **list** of
results follows the period chosen in the Period menu — that is history. The
**chart and the statistics** take the last N results whatever the period,
because a Westgard rule is read on a number of observations: whether those
thirty took three weeks or three months does not change the rule.

Under the observations the rule is not read at all and the window says `NED`,
in grey. The rules that need more points simply would not fire, and what came
out would be an `Accept` with nothing behind it.

## A result entered

Double clicking a lot opens the editor on that lot:

```
Main.on_add_result
  windows.replace("result", lambda: ui.result.UI(self, batch_id))
    Dialog.__init__                        ui/dialog.py
      tools.hide_me(self)                  built hidden
      init_fields()                        ui/result.py
      tools.center_me(self, parent)        shown in place
  Dialog.on_open()                         "Add result", the first field focused

Dialog.on_save
  tools.on_fields_control(...)             every field filled
  messagebox.askyesno(engine.ask_to_save)
  Dialog.save
    get_values()                           {column: value}, by name
    db.get_insert("results", values)       statement built from the schema
    db.write(sql, args)
      → trigger tr_results_insert          writes audit_results, with log_id
    on_cancel()
    events.notify("results", saved_id)
      → Main.on_results_changed            the chart redraws itself
```

The window that saved knows nothing about the chart. It says "results", and
whoever asked to be told redraws.

## A result corrected

The same path, through `get_update` instead of `get_insert`, and the trigger
`tr_results_update` writes the row **as it was** before the change. Put the
audit rows of one result in order and you have its life: entered at this
value, corrected to that one, excluded on that day, by whom.

```
sqlite3 -init sql/console.sql sql/biovarase.sl3
.read sql/dql/history_of_result.sql
```

Nothing in the program deletes a result. A value typed wrong is corrected, a
result on the wrong lot is moved to the right one — the lot is a combo box in
the editor — and a measurement that came out badly is excluded, which leaves
it on the chart in grey, out of the statistics, with a note saying why.

## A window opened twice

```
windows.show("batches", build)     already open → lift, focus, build nothing
windows.replace("result", build)   open → its on_cancel, then build
windows.add                        build(), remember, bind <Destroy>, on_open()
windows.forget                     <Destroy> arrived → out of the register
```

`<Destroy>` arrives however a window ends, so the register cannot be left
holding one that is gone. A Toplevel receives it for every widget inside it
as well, which is why `forget` checks that the event is the window's own.

## An error

Three layers, and each one is somewhere different.

**The statement.** `DBMS.read` and `DBMS.write` log the failure with the
statement and raise it again; `write` rolls back first. Nothing comes back as
`None`.

**The window.** What a window can answer — no row selected, a field empty, a
value that is not a date — it answers with a `messagebox` and does not raise.

**The net.** Everything else reaches `App.report_callback_exception`, which
writes the message and the traceback to the log and shows it. Tkinter calls
it from inside its own `except`, which is what `log.exception()` needs to
find the traceback.

```
python3 biovarase.py --trace
```

prints, line by line, what the program is doing and what its variables hold,
while the window is in use. It prints the data as well, so it is for the
sample database and not for a shift at the bench.

## The end

`App.on_exit` asks, closes the database and destroys the root. The log stays
where it is; the database is one file, and a copy of it is the whole
laboratory — which is what `File > Database > Backup` is for.
