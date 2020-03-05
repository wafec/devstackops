@echo off


if "%1"=="build" (
    call :build %2 %3
    goto :end
)
if "%1"=="gen" (
    call :gen %2 %3 %4
    goto :end
)
goto :end


:build
    java -cp ../bin/statemutest-all.jar statemutest.application.TestFileUtils --function settingsbuild --parameters %1 %2 destination:%3
exit /b 0


:gen
    java -cp ../bin/statemutest-all.jar statemutest.application.TestCaseGeneration --setup %1 --destination %2
exit /b 0


:end