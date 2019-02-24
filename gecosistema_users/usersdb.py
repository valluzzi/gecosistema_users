#-------------------------------------------------------------------------------
# Licence:
# Copyright (c) 2012-2019 Valerio for Gecosistema S.r.l.
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
#
# Name:        module.py
# Purpose:
#
# Author:      Luzzi Valerio
#
# Created:
#-------------------------------------------------------------------------------
from gecosistema_core import *
from gecosistema_mail import *
from gecosistema_database import *
from random import randint

class UsersDB(SqliteDB):
    """
    SqliteDB - Next version of sqlite database wrapper
    """
    version = "0.0.1"

    def __init__(self, filename="htaccess.sqlite", modules="", fileconf="", verbose=False):
        """
        Constructor
        :param filename:
        :param modules:
        :param verbose:
        """
        SqliteDB.__init__(self, filename )
        self.create_function("md5", 1, md5text)
        self.execute("""
        CREATE TABLE IF NOT EXISTS [users](mail TEXT PRIMARY KEY,name TEXT, token TEXT(32), enabled BOOL DEFAULT 0,role TEXT DEFAULT 'user');
        """)
        self.fileconf = fileconf

    def check_user_permissions(self, environ):
        """
        check_user_permissions
        """
        #check for local db
        url = normpath(environ["SCRIPT_FILENAME"])
        filedb = justpath(url) + "/htaccess.sqlite"
        #check for root db
        if not isfile(filedb):
            DOCUMENT_ROOT = environ["DOCUMENT_ROOT"] if "DOCUMENT_ROOT" in environ else leftpart(normpath(__file__),"/apps/")
            filedb = DOCUMENT_ROOT + "/htaccess.sqlite"

        HTTP_COOKIE = getCookies(environ)

        if file(filedb):

            HTTP_COOKIE["__token__"] = HTTP_COOKIE["__token__"] if "__token__" in HTTP_COOKIE else ""

            sql = """
            SELECT COUNT(*),[mail] FROM [users] 
            WHERE ('{__token__}' LIKE md5([token]||strftime('%Y-%m-%d','now')) AND [enabled])
                    OR ([mail] LIKE 'everyone' AND [enabled]);"""
            sql = sformat(sql, HTTP_COOKIE)

            [(user_enabled, mail),]  = self.execute(sql,outputmode="array")

            return mail if user_enabled else False

        return False

    def addUser(self, mail, name="", password="", role="user", enabled=False, sendmail=False):
        """
        addUser
        """
        password = md5text(password) if password else md5text("%s"%(randint(0,100000)))[:5]
        env = {
            "mail":mail,
            "name": name if name else mail,
            "password": password,
            "role":role,
            "enabled":1 if enabled else 0
        }
        sql= """
        INSERT OR IGNORE INTO [users]([mail],[name],[token],[role],[enabled]) VALUES('{mail}','{name}',md5('{mail}'||'{password}'),'{role}',{enabled});
        SELECT [token] FROM   [users] WHERE [name] ='{name}' AND [mail]='{mail}';
        """
        __token__ = self.execute(sql, env, outputmode="scalar", verbose=False)
        env["__token__"] = __token__

        #send a mail to Administrators
        administrators = self.execute("""SELECT GROUP_CONCAT([mail],',') FROM [users] WHERE [role] ='admin';""", env,
                               outputmode="scalar", verbose=False)
        if administrators and sendmail and isfile(self.fileconf):
            text = """</br>
                   {name} ask you to grant access to the Web Tool.</br>
                   If you want to enable {name} aka {mail} click on the following link:</br>
                   <a href='http://localhost/common/lib/py/users/enable.py?token={__token__}&enabled=1'>Enable {name}</a></br>
                   """
            system_mail(administrators, sformat(text, env), sformat("""User confirmation of {name}""", env), self.fileconf)

        return __token__

    def enableUser(self, token, enabled=1, sendmail=False):
        """
        enableUser
        """
        env ={
            "token":token,
            "enabled":1 if enabled else 0,
            "password":  md5text("%s"%randint(0,10000))[:5]
        }
        sql = """
        UPDATE [users] SET [enabled]={enabled},[token]=md5([mail]||'{password}') WHERE [token]='{token}';
        SELECT [mail],[name],[enabled] FROM [users]  WHERE [token]=md5([mail]||'{password}');
        """
        (mail,name,enabled) = self.execute(sql,env,outputmode='first-row',verbose=True)

        # A mail to the user
        if mail:
            text = """</br>
                    Login at <a href='http://localhost/webgis/private/{mail}'>http://localhost/webgis/</a></br>
                    Your password is:<b>{password}</b></br>
                    """

            if sendmail and isfile(self.fileconf):
                system_mail(mail, sformat(text, env), "User Credentials for the Webgis.", self.fileconf,verbose=True)
            return {
                "name":name,
                "mail":mail,
                "enabled":enabled
            }

        return False

    def getToken(self,username, password):
        """
        getToken
        """
        env = {
            "username": username,
            "password": password
        }
        sql = """
        SELECT md5([token]||strftime('%Y-%m-%d','now')) FROM [users]
            WHERE ([name] LIKE '{username}' OR [mail] LIKE '{username}')
            AND [token] LIKE md5([mail]||'{password}')
            AND [enabled];
        """
        return self.execute(sql,env,outputmode="scalar",verbose=False)


if __name__== "__main__":

    environ = {

        "SCRIPT_FILENAME":__file__,
        "HTTP_COOKIES":"__token__=D1173F96320CBEE7CAF92E6FD965D1DA;__username__:valluzzi@gmail.com"
    }

    db = UsersDB(fileconf="mail.conf")
    #print db.addUser("valerio.luzzi@gecosistema.com","Valerio Luzzi","12345678", "admin", 1)
    #token = db.addUser("valluzzi@gmail.com",sendmail=True )
    print db.enableUser('bdd8d5f81443f6271ac7e48e922ade48',sendmail=True )
    #print db.enableUser(token,sendmail=True )

    db.close()
    print "done!"