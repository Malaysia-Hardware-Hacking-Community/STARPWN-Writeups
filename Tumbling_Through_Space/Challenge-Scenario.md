Sometimes a glider needs to know not to ask too many questions about who is behind a brief. This is one of those cases.

Our friends are having difficulties with one of their satellites. It appears it has been struck by space debris and is now tumbling out of control. This is where you come in. The Attitude Determination and Control System (ADCS) is still online, but the automated detumbling sequence has failed. You will have to compute the correct control torques manually.

They've provided you with all you need, just need to connect to their shell.

You'll be told the satellite's moments of inertia (Ixx, Iyy, Izz) and current angular velocities (ωx, ωy, ωz). Submit four space-separated values per line:

	Tx  Ty  Tz  duration

where Tx/Ty/Tz are the body-frame torques in N·m and duration is the burn length in seconds (0 < duration ≤ 100). The torque-vector magnitude is capped at 1.0 N·m per the thruster spec.

Detumbling succeeds when |ω| drops below 0.01 rad/s.

You get five attempts per connection; reconnect to retry with a fresh tumble state.
