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
from gecosistema_database import *

class UsersDB(SqliteDB):
    """
    SqliteDB - Next version of sqlite database wrapper
    """
    version = "0.0.1"

    def __init__(self, filename="htaccess.sqlite", modules="", verbose=False):
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


if __name__== "__main__":

    environ = {

        "SCRIPT_FILENAME":__file__,
        "HTTP_COOKIES":"__token__=D1173F96320CBEE7CAF92E6FD965D1DA;__username__:valluzzi@gmail.com"
    }

    db = UsersDB()
    print db.check_user_permissions(environ)
    db.close()
    print "done!"